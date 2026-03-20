"""
ai_selector.py
Uses Gemini (or OpenRouter fallback) to pick the most viral/engaging article.
Tracks post history to prevent repeating the same article within 30 days.
Set GEMINI_API_KEY or OPENROUTER_API_KEY in .env
Falls back gracefully if no key is set.
"""

import os
import json
import hashlib
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# ── History config ─────────────────────────────────────────────────────────────
HISTORY_FILE    = "post_history.json"
HISTORY_DAYS    = 30   # don't repeat articles within this window
MAX_HISTORY     = 200  # max entries to keep


SELECTION_PROMPT = """You are a viral health content strategist for Facebook.

Given these health news articles, select the ONE most likely to get high engagement 
(shares, reactions, comments) on Facebook from a general health-conscious audience.

Consider:
- Emotional resonance (surprising, hopeful, urgent, relatable)
- Broad audience appeal (not too niche or technical)  
- Actionable or immediately useful information
- Strong hook potential
- Topic variety — prefer articles on different topics than recently posted

Articles:
{articles_list}

Respond ONLY with valid JSON in this exact format (no other text):
{{
  "selected_index": <number 0-based>,
  "reason": "<one sentence why this article wins>"
}}"""


# ── History management ─────────────────────────────────────────────────────────

def _article_hash(title: str) -> str:
    """Generate a short hash from article title for deduplication."""
    return hashlib.md5(title.lower().strip().encode()).hexdigest()[:12]


def _load_history() -> list:
    """Load post history from file."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE) as f:
            return json.load(f)
    except Exception:
        return []


def _save_history(history: list):
    """Save post history to file, keeping only recent entries."""
    cutoff = (datetime.now() - timedelta(days=HISTORY_DAYS)).isoformat()
    recent = [h for h in history if h.get("date", "") >= cutoff]
    recent = recent[-MAX_HISTORY:]
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(recent, f, indent=2)
    except Exception as e:
        print(f"  ⚠️  Could not save history: {e}")


def save_posted_article(article: dict):
    """Call this after successfully posting to record the article."""
    history = _load_history()
    history.append({
        "hash":  _article_hash(article["title"]),
        "title": article["title"][:100],
        "date":  datetime.now().isoformat(),
    })
    _save_history(history)
    print(f"  📝 Saved to history: {article['title'][:60]}...")


def _filter_already_posted(articles: list) -> list:
    """Remove articles that were posted within the last HISTORY_DAYS days."""
    history     = _load_history()
    posted_hash = {h["hash"] for h in history}
    cutoff      = (datetime.now() - timedelta(days=HISTORY_DAYS)).isoformat()
    recent_hash = {
        h["hash"] for h in history
        if h.get("date", "") >= cutoff
    }

    filtered = [a for a in articles if _article_hash(a["title"]) not in recent_hash]

    removed = len(articles) - len(filtered)
    if removed:
        print(f"  🚫 Filtered out {removed} recently posted articles.")

    if not filtered:
        print("  ⚠️  All articles were recently posted — resetting filter for today.")
        return articles  # fallback: use all to avoid empty selection

    return filtered


# ── Article selection ──────────────────────────────────────────────────────────

def _build_articles_list(articles: list[dict]) -> str:
    lines = []
    for i, a in enumerate(articles):
        lines.append(f"{i}. [{a['source']}] {a['title']}")
        if a.get("summary"):
            lines.append(f"   Summary: {a['summary'][:150]}")
    return "\n".join(lines)


def _select_via_gemini(articles: list[dict]) -> dict | None:
    if not GEMINI_API_KEY:
        return None
    try:
        prompt = SELECTION_PROMPT.format(articles_list=_build_articles_list(articles))
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30,
        )
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        text = text.strip().replace("```json", "").replace("```", "")
        return json.loads(text)
    except Exception as e:
        print(f"  ⚠️  Gemini selector error: {e}")
        print(f"  ⚠️  Response: {resp.text[:300] if 'resp' in locals() else 'no response'}")
        return None


def _select_via_openrouter(articles: list[dict]) -> dict | None:
    if not OPENROUTER_API_KEY:
        return None
    try:
        prompt = SELECTION_PROMPT.format(articles_list=_build_articles_list(articles))
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type":  "application/json",
            },
            json={
                "model":    "mistralai/mistral-7b-instruct:free",
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        text = resp.json()["choices"][0]["message"]["content"]
        text = text.strip().replace("```json", "").replace("```", "")
        return json.loads(text)
    except Exception as e:
        print(f"  ⚠️  OpenRouter selector error: {e}")
        return None


def _heuristic_select(articles: list[dict]) -> dict:
    keywords = [
        "study", "reveals", "proven", "secret", "boost", "reduce", "natural",
        "doctors", "warning", "simple", "easy", "new", "breakthrough", "risk",
        "prevent", "cure", "health", "you should", "everyone",
    ]
    best_idx, best_score = 0, -1
    for i, a in enumerate(articles):
        title_lower = a["title"].lower()
        score = sum(1 for kw in keywords if kw in title_lower)
        if len(a["title"]) < 80:
            score += 1
        if score > best_score:
            best_score = score
            best_idx   = i
    return {"selected_index": best_idx, "reason": "heuristic keyword scoring"}


def select_best_article(articles: list[dict]) -> dict | None:
    if not articles:
        return None

    # ── Deduplicate against post history ──────────────────────────
    fresh_articles = _filter_already_posted(articles)

    result = None
    if GEMINI_API_KEY:
        print("  🤖 Using Gemini to select article...")
        result = _select_via_gemini(fresh_articles)
    elif OPENROUTER_API_KEY:
        print("  🤖 Using OpenRouter to select article...")
        result = _select_via_openrouter(fresh_articles)
    else:
        print("  ⚠️  No AI key set — using heuristic selection.")

    if not result:
        result = _heuristic_select(fresh_articles)

    idx    = result.get("selected_index", 0)
    reason = result.get("reason", "")
    print(f"  ✅ Selected index {idx}: {reason}")

    if 0 <= idx < len(fresh_articles):
        return fresh_articles[idx]
    return fresh_articles[0]


if __name__ == "__main__":
    test_articles = [
        {"title": "5 Superfoods Proven to Boost Your Immune System", "source": "Healthline", "summary": ""},
        {"title": "New Study Reveals Coffee May Reduce Alzheimer Risk", "source": "WebMD", "summary": ""},
        {"title": "Simple Breathing Exercise Reduces Anxiety in Minutes", "source": "MNT", "summary": ""},
    ]
    best = select_best_article(test_articles)
    print(f"\nSelected: {best['title']}")
    save_posted_article(best)
    print("History saved.")
