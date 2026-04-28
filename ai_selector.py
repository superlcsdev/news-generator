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


SELECTION_PROMPT = """You are a health content strategist for a Facebook page run by a USANA health
supplement distributor targeting Filipino professionals in Singapore and the Philippines.

Given these health articles, select the ONE most likely to get high engagement
AND that aligns with a natural health and nutrition business.

PRIORITISE articles about:
- Nutrition, vitamins, minerals, antioxidants, superfoods
- Immune health, gut health, cellular health, inflammation
- Sleep quality, stress management, energy and fatigue
- Exercise, movement, physical performance, recovery
- Preventive health, healthy ageing, longevity
- Mental health (stress, burnout, wellbeing) — not psychiatric drugs
- General wellness tips and healthy lifestyle habits

REJECT articles about:
- Prescription drugs, weight-loss medications (Ozempic, Mounjaro, Wegovy, etc.)
- Pharmaceutical products, drug trials, clinical drug studies
- Any specific supplement, skincare, or health brand other than general nutrition
- Surgery, medical procedures, hospital treatments
- Diseases, illnesses, or conditions as the main focus (cancer, diabetes news, etc.)
- Political health policy or government healthcare funding

Articles:
{articles_list}

Respond ONLY with valid JSON:
{{
  "selected_index": <number 0-based>,
  "reason": "<one sentence why this fits a natural health business>"
}}"""


# ── USANA business content filter ─────────────────────────────────────────────
# Hard block — these topics directly conflict with a supplement business
HARD_BLOCKED_KEYWORDS = [
    # Weight loss drugs — direct competitor/conflict
    "ozempic", "wegovy", "mounjaro", "tirzepatide", "semaglutide",
    "glp-1", "glp1", "weight loss drug", "weight loss medication",
    "weight loss pill", "diet pill", "weight loss injection",
    # Pharma / prescription drugs
    "prescription drug", "fda approved drug", "clinical trial", "drug trial",
    "antidepressant", "antipsychotic", "statin", "blood thinner",
    "chemotherapy", "immunotherapy", "biological drug",
    # Competitor supplement/skincare brands
    "herbalife", "amway", "shaklee", "isagenix", "nuskin", "nu skin",
    "forever living", "arbonne", "advocare", "beachbody", "optavia",
    # Medical procedures
    "bariatric surgery", "gastric bypass", "gastric sleeve", "liposuction",
    "botox", "filler", "cosmetic surgery", "weight loss surgery",
    # Harmful / off-brand topics
    "war", "conflict", "attack", "killed", "shooting",
    "election", "scandal", "arrested",
]

# Soft block — deprioritise (not outright removed, but scored low)
SOFT_BLOCKED_KEYWORDS = [
    "drug", "medication", "pharmaceutical", "hospital treatment",
    "surgery", "chemotherapy", "dialysis", "transplant",
    "cancer treatment", "diabetes drug", "insulin",
]

# USANA-aligned topics — boost score when present
PREFERRED_KEYWORDS = [
    # Nutrition
    "nutrition", "nutrient", "vitamin", "mineral", "antioxidant",
    "omega-3", "omega3", "protein", "fibre", "fiber", "probiotic",
    "superfood", "plant-based", "whole food", "gut health", "microbiome",
    # Health pillars that USANA addresses
    "immune", "immunity", "cellular health", "inflammation", "antioxidant",
    "sleep", "energy", "fatigue", "stress", "cortisol", "burnout",
    "muscle", "bone health", "heart health", "cardiovascular",
    # Lifestyle / preventive
    "exercise", "workout", "movement", "walking", "fitness",
    "healthy ageing", "longevity", "prevention", "wellness",
    "mental health", "wellbeing", "self-care", "mindfulness",
    # Audience-relevant
    "nurses", "professionals", "shift work", "sedentary", "desk job",
    "study reveals", "research shows", "new study", "scientists find",
    "natural", "holistic", "diet", "weight management",
]


def _is_business_safe(article: dict) -> bool:
    """
    Hard filter — returns False if article conflicts with USANA business.
    Checks title + summary against blocked keywords.
    """
    text = (article.get("title", "") + " " + article.get("summary", "")).lower()
    for kw in HARD_BLOCKED_KEYWORDS:
        if kw in text:
            print(f"  🚫 Blocked (business conflict): '{kw}' — {article['title'][:60]}")
            return False
    return True


def _business_score(article: dict) -> int:
    """
    Score article alignment with USANA business.
    Higher = better fit. Used in heuristic fallback.
    """
    text  = (article.get("title", "") + " " + article.get("summary", "")).lower()
    score = 0
    for kw in PREFERRED_KEYWORDS:
        if kw in text:
            score += 2
    for kw in SOFT_BLOCKED_KEYWORDS:
        if kw in text:
            score -= 3
    # Short titles tend to be more shareable
    if len(article.get("title", "")) < 80:
        score += 1
    return score




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
    """Score by USANA business alignment + virality."""
    best_idx, best_score = 0, -1
    for i, a in enumerate(articles):
        score = _business_score(a)
        if score > best_score:
            best_score = score
            best_idx   = i
    return {"selected_index": best_idx, "reason": "heuristic USANA-aligned scoring"}


def select_best_article(articles: list[dict]) -> dict | None:
    if not articles:
        return None

    # ── Step 1: Hard filter — remove business-conflicting articles ────────────
    safe = [a for a in articles if _is_business_safe(a)]
    removed = len(articles) - len(safe)
    if removed:
        print(f"  🛡️  Removed {removed} business-conflicting articles "
              f"(drugs, competitor brands, pharma).")
    if not safe:
        print("  ⚠️  All articles were business-conflicting — using all as fallback.")
        safe = articles

    print(f"  📊 {len(safe)}/{len(articles)} articles passed business filter.")

    # ── Step 2: Deduplicate against post history ──────────────────────────────
    fresh = _filter_already_posted(safe)

    # ── Step 3: AI selection ──────────────────────────────────────────────────
    result = None
    if GEMINI_API_KEY:
        print("  🤖 Using Gemini to select article...")
        result = _select_via_gemini(fresh)
    elif OPENROUTER_API_KEY:
        print("  🤖 Using OpenRouter to select article...")
        result = _select_via_openrouter(fresh)
    else:
        print("  ⚠️  No AI key — using heuristic selection.")

    if not result:
        result = _heuristic_select(fresh)

    idx    = result.get("selected_index", 0)
    reason = result.get("reason", "")
    print(f"  ✅ Selected index {idx}: {reason}")

    if 0 <= idx < len(fresh):
        return fresh[idx]
    return fresh[0]


if __name__ == "__main__":
    test_articles = [
        {"title": "Ozempic vs Mounjaro: Which Drug Causes More Muscle Loss?",       "source": "WebMD",     "summary": "study on weight loss drugs"},
        {"title": "5 Superfoods Proven to Boost Your Immune System Naturally",      "source": "Healthline","summary": "nutrition and immunity"},
        {"title": "New Study: Vitamin D Deficiency Linked to Chronic Fatigue",      "source": "MNT",       "summary": "vitamin D and energy levels"},
        {"title": "Why Filipino Shift Workers Are at Higher Risk of Burnout",        "source": "CNA",       "summary": "stress and sleep deprivation"},
        {"title": "Herbalife Shake vs Whole Foods: Which Is Better for Gut Health?","source": "Blog",      "summary": "supplement comparison"},
    ]
    print("Testing business filter:")
    best = select_best_article(test_articles)
    print(f"\nSelected: {best['title']}")
