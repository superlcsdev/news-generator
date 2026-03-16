"""
ai_selector.py
Uses Gemini (or OpenRouter fallback) to pick the most viral/engaging article.
Set GEMINI_API_KEY or OPENROUTER_API_KEY in .env
Falls back gracefully if no key is set.
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

SELECTION_PROMPT = """You are a viral health content strategist for Facebook.

Given these health news articles, select the ONE most likely to get high engagement 
(shares, reactions, comments) on Facebook from a general health-conscious audience.

Consider:
- Emotional resonance (surprising, hopeful, urgent, relatable)
- Broad audience appeal (not too niche or technical)  
- Actionable or immediately useful information
- Strong hook potential

Articles:
{articles_list}

Respond ONLY with valid JSON in this exact format (no other text):
{{
  "selected_index": <number 0-based>,
  "reason": "<one sentence why this article wins>"
}}"""


def _build_articles_list(articles: list[dict]) -> str:
    lines = []
    for i, a in enumerate(articles):
        lines.append(f"{i}. [{a['source']}] {a['title']}")
        if a.get("summary"):
            lines.append(f"   Summary: {a['summary'][:150]}")
    return "\n".join(lines)


def _select_via_gemini(articles: list[dict]) -> dict | None:
    """Call Gemini Flash to select best article."""
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
        return None


def _select_via_openrouter(articles: list[dict]) -> dict | None:
    """Call OpenRouter as fallback."""
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
    """
    Simple heuristic fallback — scores titles by engagement keywords.
    No API needed.
    """
    keywords = [
        "study", "reveals", "proven", "secret", "boost", "reduce", "natural",
        "doctors", "warning", "simple", "easy", "new", "breakthrough", "risk",
        "prevent", "cure", "health", "you should", "everyone",
    ]
    best_idx   = 0
    best_score = -1
    for i, a in enumerate(articles):
        title_lower = a["title"].lower()
        score = sum(1 for kw in keywords if kw in title_lower)
        # Prefer shorter, punchy titles
        if len(a["title"]) < 80:
            score += 1
        if score > best_score:
            best_score = i
            best_idx   = i
    return {"selected_index": best_idx, "reason": "heuristic keyword scoring"}


def select_best_article(articles: list[dict]) -> dict | None:
    """
    Try Gemini → OpenRouter → heuristic fallback.
    Returns the selected article dict.
    """
    if not articles:
        return None

    result = None

    if GEMINI_API_KEY:
        print("  🤖 Using Gemini to select article...")
        result = _select_via_gemini(articles)
    elif OPENROUTER_API_KEY:
        print("  🤖 Using OpenRouter to select article...")
        result = _select_via_openrouter(articles)
    else:
        print("  ⚠️  No AI key set — using heuristic selection.")

    if not result:
        result = _heuristic_select(articles)

    idx    = result.get("selected_index", 0)
    reason = result.get("reason", "")
    print(f"  ✅ Selected index {idx}: {reason}")

    if 0 <= idx < len(articles):
        return articles[idx]
    return articles[0]


if __name__ == "__main__":
    # Quick test with dummy articles
    test_articles = [
        {"title": "5 Superfoods Proven to Boost Your Immune System", "source": "Healthline", "summary": ""},
        {"title": "New Study Reveals Coffee May Reduce Alzheimer Risk", "source": "WebMD", "summary": ""},
        {"title": "Simple Breathing Exercise Reduces Anxiety in Minutes", "source": "MNT", "summary": ""},
    ]
    best = select_best_article(test_articles)
    print(f"\nSelected: {best['title']}")
