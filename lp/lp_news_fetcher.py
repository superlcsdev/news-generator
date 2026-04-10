"""
lp/lp_news_fetcher.py
Fetches and scores news for @lawrenceprecioussia audience.

Purpose: Find articles that inspire Filipinos to think about building
another income source — motivated by possibility, not fear.
Tone target: "This is why it's worth it" not "This is why you should be scared."
"""

import os
import json
import re
import hashlib
import feedparser
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

# ── RSS Sources — broadened to include inspiration + business building ─────────
RSS_SOURCES = [
    # Philippine business — high signal for OFW/professional audience
    {"url": "https://businessmirror.com.ph/feed/",              "source": "BusinessMirror",   "weight": 1.3},
    {"url": "https://www.bworldonline.com/feed/",               "source": "BusinessWorld PH", "weight": 1.3},
    # Entrepreneurship and career — globally relevant
    {"url": "https://feeds.feedburner.com/entrepreneur/latest", "source": "Entrepreneur",     "weight": 1.3},
    {"url": "https://hbr.org/rss/topic/entrepreneurship",       "source": "HBR Entrepreneurship", "weight": 1.2},
    {"url": "https://hbr.org/rss/topic/work-life-balance",      "source": "HBR Work-Life",    "weight": 1.2},
    {"url": "https://hbr.org/rss/topic/finance",                "source": "HBR Finance",      "weight": 1.1},
    # Singapore working life
    {"url": "https://www.channelnewsasia.com/rss/8395986",      "source": "CNA Singapore",    "weight": 1.1},
    # Inc. Magazine — entrepreneurship stories and inspiration
    {"url": "https://www.inc.com/rss",                          "source": "Inc Magazine",     "weight": 1.2},
    # Forbes entrepreneurship
    {"url": "https://www.forbes.com/feeds/news/rss/entrepreneurship.xml", "source": "Forbes Entrepreneurs", "weight": 1.1},
    # Philippine general — lower weight, higher noise
    {"url": "https://newsinfo.inquirer.net/feed",               "source": "Inquirer",         "weight": 0.8},
]

# ── HIGH VALUE keywords — motivation and opportunity framing ──────────────────
HIGH_VALUE = {
    # Building income — the core theme
    "side hustle": 5, "extra income": 5, "multiple income": 5,
    "passive income": 5, "second income": 5, "income stream": 5,
    "financial freedom": 5, "financial independence": 4,
    "entrepreneur": 4, "entrepreneurship": 4,
    "small business": 4, "startup": 3, "self employed": 4,
    "freelance": 4, "freelancer": 4,
    # Career and work pain points — signals "maybe I should build something"
    "burnout": 4, "work life balance": 4, "resignation": 3,
    "quiet quitting": 4, "overworked": 4, "underpaid": 4,
    "layoff": 4, "retrenchment": 4, "redundancy": 4,
    "job security": 4, "career change": 4,
    # Financial reality — cost of living awareness
    "salary": 3, "income": 3, "wages": 3, "savings": 4,
    "cost of living": 4, "inflation": 3, "peso": 2,
    "remittance": 3, "family income": 4,
    # OFW and Singapore — audience context
    "ofw": 4, "overseas filipino": 4,
    "singapore worker": 3, "work pass": 3,
    "philippines": 1, "singapore": 1, "filipino": 2, "pinoy": 2,
    # Inspiration signals
    "success story": 4, "built": 3, "founder": 3,
    "opportunity": 3, "growth": 2, "invest": 3, "wealth": 3,
}

# ── NEGATIVE keywords — reject these immediately ──────────────────────────────
NEGATIVE_KEYWORDS = [
    # Violence, crime, disaster
    "murder", "crime", "rape", "scandal", "corruption",
    "war", "bomb", "terror", "shooting", "earthquake",
    "typhoon", "flood", "death toll", "killed", "casualties",
    # Sports
    "wnba", "nba", "pba", "nfl", "fifa", "ufc",
    "basketball game", "football match", "tennis tournament",
    "golf tournament", "boxing match",
    # Entertainment / celebrity
    "celebrity", "showbiz", "box office", "concert tour",
    "album release", "grammy", "oscar", "festival parade",
    # Pure fear/negativity — no motivational angle possible
    "recession fears", "market crash", "bank collapse",
    "mass layoff", "factory closure",
    # Geopolitics
    "trump", "iran", "missile", "nuclear", "military strike",
    "senate hearing", "impeach",
    # Off-topic
    "food festival", "tourism", "recipe", "restaurant review",
]

# ── POSITIVE BOOST — articles with these get extra score ─────────────────────
POSITIVE_BOOST = [
    "how to", "tips", "guide", "build", "grow", "start",
    "success", "achieve", "opportunity", "future", "freedom",
    "inspire", "motivate", "story", "journey", "playbook",
]

# Minimum score — must genuinely match audience themes
MIN_SCORE = 4

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

    # Hard reject
    for neg in NEGATIVE_KEYWORDS:
        if neg in text:
            return -1

    # Base score from high-value keywords
    score = sum(pts for kw, pts in HIGH_VALUE.items() if kw in text)

    # Positive boost — articles about building/growing/inspiring score higher
    boost = sum(1 for word in POSITIVE_BOOST if word in text)
    score += min(boost, 4)  # cap boost at 4 points

    # Recency bonus
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
