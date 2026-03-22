"""
lp/lp_news_fetcher.py
Fetches and scores news for @lawrenceprecioussia audience.
Matches the pattern from news_fetcher.py — same RSS + scoring approach.
Uses a SEPARATE post history file (lp_post_history.json) so it never
conflicts with the health news post_history.json.
"""

import os
import json
import re
import hashlib
import feedparser
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

# ── RSS Sources — focused on working professional and financial content ────────
RSS_SOURCES = [
    # Philippine business and financial news — highest relevance
    {"url": "https://businessmirror.com.ph/feed/",                 "source": "BusinessMirror",   "weight": 1.3},
    {"url": "https://www.bworldonline.com/feed/",                  "source": "BusinessWorld PH", "weight": 1.3},
    # Singapore working life
    {"url": "https://www.channelnewsasia.com/rss/8395986",         "source": "CNA Singapore",    "weight": 1.2},
    # Global work/career/leadership
    {"url": "https://hbr.org/rss/topic/work-life-balance",        "source": "HBR Work-Life",    "weight": 1.2},
    {"url": "https://feeds.feedburner.com/entrepreneur/latest",    "source": "Entrepreneur",     "weight": 1.0},
    # Philippine general news — lower weight, more noise
    {"url": "https://newsinfo.inquirer.net/feed",                  "source": "Inquirer",         "weight": 0.8},
    # Rappler removed — too much entertainment/politics noise for this audience
]

# ── Viral scoring keywords — tuned for LP audience pain points ───────────────
HIGH_VALUE = {
    # Financial reality — highest value
    "salary": 4, "income": 4, "wages": 3, "minimum wage": 4,
    "savings": 4, "debt": 3, "inflation": 4, "cost of living": 4,
    "peso": 3, "exchange rate": 3,
    # OFW and Singapore working life
    "ofw": 4, "overseas filipino": 4, "remittance": 3,
    "singapore worker": 4, "foreign worker": 3, "work pass": 3,
    # Work-life pain points
    "burnout": 4, "work life balance": 4, "resignation": 3,
    "quiet quitting": 3, "remote work": 3, "work from home": 3,
    "overworked": 3, "underpaid": 4, "job stress": 3,
    "layoff": 4, "retrenchment": 4, "redundancy": 3,
    # Building something
    "side hustle": 4, "extra income": 4, "entrepreneur": 3,
    "small business": 3, "freelance": 3,
    "self employed": 3, "startup": 2,
    # Family and time
    "work family balance": 4, "parenting": 2, "family income": 3,
    "financial stress": 4, "money stress": 4,
    # Geography — lower value, just context
    "philippines": 1, "singapore": 1, "filipino": 2, "pinoy": 2,
}

# Hard reject — article immediately discarded if any of these appear in title/summary
NEGATIVE_KEYWORDS = [
    # Violence and disaster
    "murder", "crime", "rape", "scandal", "corruption",
    "war", "bomb", "terror", "shooting", "earthquake",
    "typhoon", "flood", "death toll", "killed",
    # Sports
    "wnba", "nba", "pba", "nfl", "fifa", "ufc",
    "basketball game", "football game", "tennis tournament",
    "golf tournament", "boxing match", "athlete",
    # Entertainment / celebrity
    "celebrity", "actor", "actress", "showbiz", "box office",
    "concert tour", "album release", "grammy", "oscar",
    "richard mercado", "festival parade",
    # Geopolitics — too divisive, off-brand
    "trump", "iran", "missile", "nuclear", "military strike",
    "senate hearing", "impeach", "opposition leader",
    # Off-topic lifestyle
    "strawberry festival", "food festival", "tourism",
    "recipe", "restaurant review",
]

# Minimum score — must genuinely match audience keywords, not just geography
# Score of 5+ means at least one strong keyword (salary=4 + philippines=1)
MIN_SCORE = 5

# Separate history file — never conflicts with health news post_history.json
HISTORY_FILE = "lp_post_history.json"
HISTORY_DAYS = 30
MAX_HISTORY  = 200


def _hash(title: str) -> str:
    return hashlib.md5(title.lower().strip().encode()).hexdigest()[:12]


def _load_history() -> list:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE) as f:
            return json.load(f)
    except Exception:
        return []


def save_posted_article(article: dict):
    """Call after successfully posting to prevent repeating within 30 days."""
    history = _load_history()
    history.append({
        "hash":  _hash(article["title"]),
        "title": article["title"][:100],
        "date":  datetime.now().isoformat(),
    })
    cutoff  = (datetime.now() - timedelta(days=HISTORY_DAYS)).isoformat()
    recent  = [h for h in history if h.get("date", "") >= cutoff][-MAX_HISTORY:]
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(recent, f, indent=2)
        print(f"  📝 LP history saved: {article['title'][:60]}...")
    except Exception as e:
        print(f"  ⚠️ Could not save LP history: {e}")


def _already_posted(title: str) -> bool:
    cutoff  = (datetime.now() - timedelta(days=HISTORY_DAYS)).isoformat()
    history = _load_history()
    recent  = {h["hash"] for h in history if h.get("date", "") >= cutoff}
    return _hash(title) in recent


def _score(article: dict, weight: float) -> int:
    text = (article.get("title", "") + " " + article.get("summary", "")).lower()

    for neg in NEGATIVE_KEYWORDS:
        if neg in text:
            return -1

    score = sum(pts for kw, pts in HIGH_VALUE.items() if kw in text)

    # Recency bonus — same as your ai_selector.py logic
    pub = article.get("published_parsed")
    if pub:
        try:
            age_h = (datetime.now(timezone.utc) -
                     datetime(*pub[:6], tzinfo=timezone.utc)).total_seconds() / 3600
            score += 5 if age_h < 24 else (2 if age_h < 48 else 0)
        except Exception:
            pass

    return int(score * weight)


def fetch_top_articles(max_articles: int = 5) -> list[dict]:
    """
    Fetch, score, and deduplicate news articles for the LP page.
    Returns top N sorted by score.
    """
    candidates = []

    for src in RSS_SOURCES:
        try:
            feed = feedparser.parse(src["url"])
            for entry in feed.entries[:15]:
                url     = entry.get("link", "")
                title   = entry.get("title", "").strip()
                summary = re.sub(r"<[^>]+>", "", entry.get("summary", "")).strip()

                if not title or not url:
                    continue
                if _already_posted(title):
                    continue

                article = {
                    "title":            title,
                    "url":              url,
                    "summary":          summary[:500],
                    "source":           src["source"],
                    "published_parsed": entry.get("published_parsed"),
                }

                score = _score(article, src["weight"])
                if score < MIN_SCORE:
                    continue

                article["score"] = score
                candidates.append(article)

        except Exception as e:
            print(f"  ⚠️ LP RSS error ({src['source']}): {e}")

    candidates.sort(key=lambda x: x["score"], reverse=True)
    top = candidates[:max_articles]

    print(f"  ✅ LP news: {len(candidates)} fetched, top {len(top)} selected.")
    for a in top:
        print(f"     [{a['score']:>3}] {a['source']:20} {a['title'][:55]}")

    return top
