"""
news_fetcher.py
Fetches top health articles from free RSS feeds.
No API key required for basic operation.
Optional: set NEWS_API_KEY in .env for more sources.
"""

import os
import feedparser
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

# Free RSS feeds — no key needed
RSS_FEEDS = [
    {"url": "https://feeds.feedburner.com/webmd/HealthAndWellness",  "source": "WebMD"},
    {"url": "https://www.healthline.com/rss/health-news",             "source": "Healthline"},
    {"url": "https://rss.medicalnewstoday.com/featurednews.xml",      "source": "MedicalNewsToday"},
    {"url": "https://www.who.int/rss-feeds/news-english.xml",         "source": "WHO"},
    {"url": "https://feeds.reuters.com/reuters/healthNews",           "source": "Reuters Health"},
]

MAX_ARTICLES_PER_FEED = 5
MAX_TOTAL_ARTICLES    = 20


def _parse_feed(feed_info: dict) -> list[dict]:
    """Parse a single RSS feed and return article dicts."""
    articles = []
    try:
        feed = feedparser.parse(feed_info["url"])
        for entry in feed.entries[:MAX_ARTICLES_PER_FEED]:
            articles.append({
                "title":       entry.get("title", "").strip(),
                "url":         entry.get("link", ""),
                "summary":     entry.get("summary", "")[:300],
                "source":      feed_info["source"],
                "category":    "health",
                "published":   entry.get("published", ""),
            })
    except Exception as e:
        print(f"  ⚠️  RSS feed error ({feed_info['source']}): {e}")
    return articles


def _fetch_newsapi(query: str = "health wellness nutrition", page_size: int = 10) -> list[dict]:
    """Fetch from NewsAPI if key is configured."""
    if not NEWS_API_KEY:
        return []
    try:
        resp = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q":        query,
                "language": "en",
                "sortBy":   "popularity",
                "pageSize": page_size,
                "apiKey":   NEWS_API_KEY,
            },
            timeout=15,
        )
        data = resp.json()
        articles = []
        for a in data.get("articles", []):
            if not a.get("title") or a["title"] == "[Removed]":
                continue
            articles.append({
                "title":    a["title"].strip(),
                "url":      a.get("url", ""),
                "summary":  (a.get("description") or "")[:300],
                "source":   a.get("source", {}).get("name", "NewsAPI"),
                "category": "health",
                "published": a.get("publishedAt", ""),
            })
        return articles
    except Exception as e:
        print(f"  ⚠️  NewsAPI error: {e}")
        return []


def fetch_top_articles() -> list[dict]:
    """Fetch articles from all configured sources and return deduplicated list."""
    all_articles = []

    # RSS feeds
    for feed in RSS_FEEDS:
        articles = _parse_feed(feed)
        all_articles.extend(articles)
        print(f"  📰 {feed['source']}: {len(articles)} articles")

    # NewsAPI (optional)
    if NEWS_API_KEY:
        na_articles = _fetch_newsapi()
        all_articles.extend(na_articles)
        print(f"  📰 NewsAPI: {len(na_articles)} articles")

    # Deduplicate by title
    seen   = set()
    unique = []
    for a in all_articles:
        key = a["title"].lower()[:60]
        if key not in seen and a["title"]:
            seen.add(key)
            unique.append(a)

    print(f"  📊 Total unique articles: {len(unique)}")
    return unique[:MAX_TOTAL_ARTICLES]


if __name__ == "__main__":
    articles = fetch_top_articles()
    for i, a in enumerate(articles, 1):
        print(f"{i:2}. [{a['source']}] {a['title'][:80]}")
