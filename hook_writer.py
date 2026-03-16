"""
hook_writer.py
Generates an engaging Facebook hook caption for an article.
Uses Gemini → OpenRouter → template fallback.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

HOOK_PROMPT = """You are a Facebook health content writer specialising in viral posts.

Write a compelling Facebook post caption for this health news article.
The caption must:
- Start with a hook (question, shocking fact, or bold statement) — NO emojis in first line
- Be 3–5 sentences max
- End with a call to action (e.g. "Share this with someone who needs it!")
- Use 2–3 relevant emojis naturally throughout
- Sound human, warm, and relatable — NOT like a news headline
- Do NOT mention the source website

Article title  : {title}
Article summary: {summary}

Write ONLY the caption. No preamble, no quotes around it."""


def _call_gemini(prompt: str) -> str | None:
    if not GEMINI_API_KEY:
        return None
    try:
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30,
        )
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"  ⚠️  Gemini hook error: {e}")
        return None


def _call_openrouter(prompt: str) -> str | None:
    if not OPENROUTER_API_KEY:
        return None
    try:
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
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"  ⚠️  OpenRouter hook error: {e}")
        return None


def _template_hook(article: dict) -> str:
    """Fallback template-based hook when no AI key is available."""
    title = article["title"]
    templates = [
        f"Did you know? 👀 {title}. This is something everyone should be aware of! "
        f"💪 Small changes can make a BIG difference to your health. Share this with someone who needs it! ❤️",

        f"This changes everything! 🔥 {title}. "
        f"Your health is your greatest wealth — don't ignore this. 🌿 "
        f"Tag a friend who needs to see this!",

        f"Health alert! ⚠️ {title}. "
        f"The science is clear — and it's easier than you think to take action. 💚 "
        f"Save this post and share it with your loved ones!",
    ]
    import hashlib
    idx = int(hashlib.md5(title.encode()).hexdigest(), 16) % len(templates)
    return templates[idx]


def generate_hook(article: dict) -> str:
    """Generate a Facebook hook caption for the article."""
    prompt = HOOK_PROMPT.format(
        title   = article.get("title", ""),
        summary = article.get("summary", "No summary available."),
    )

    hook = None
    if GEMINI_API_KEY:
        hook = _call_gemini(prompt)
    elif OPENROUTER_API_KEY:
        hook = _call_openrouter(prompt)

    if not hook:
        print("  ⚠️  Using template hook (no AI key configured).")
        hook = _template_hook(article)

    # Append article URL if available
    url = article.get("url", "")
    if url:
        hook = f"{hook}\n\n🔗 {url}"

    return hook


if __name__ == "__main__":
    test_article = {
        "title":   "New Study: Daily 20-Minute Walk Reduces Heart Disease Risk by 35%",
        "summary": "Researchers found that consistent moderate walking significantly lowers cardiovascular risk.",
        "url":     "https://example.com/article",
    }
    print(generate_hook(test_article))
