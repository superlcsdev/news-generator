"""
hook_writer.py
Generates an engaging Facebook hook caption for a health article.
Audience: Filipino professionals (nurses, IT, engineers, etc.) in SG + PH.
Tone: Peer-to-peer, ambitious, analytical — not OFW hardship framing.
Uses Gemini → OpenRouter → template fallback.
"""

import os
import hashlib
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

HOOK_PROMPT = """You are a Facebook health content writer for an audience of Filipino professionals 
— nurses, IT professionals, engineers, architects, pharmacists, and other degree-holding 
career-driven individuals based in Singapore and the Philippines.

Write a compelling Facebook post caption for this health news article.

Tone guidelines:
- Speak to their professional identity and ambition — not hardship or struggle
- Frame health as performance, productivity, and career longevity — not survival
- Peer-to-peer voice — like a smart colleague sharing something useful
- Use data or surprising facts when relevant — this audience is analytical
- Very occasional Filipino word for warmth (max 1 per post, only if completely natural)
  e.g. "Kaya mo ito." — never heavy Taglish
- Never mention OFW hardship, remittance, or domestic worker context

Structure:
- Line 1: Hook — surprising stat, professional angle, or sharp observation. NO emoji on first line.
- Lines 2–3: Brief insight connecting to their professional life
- Last line: CTA that respects their intelligence (not "share with someone who needs it")

Use 2–3 emojis naturally. Max 4 sentences total. Do NOT mention the source website.

Article title  : {title}
Article summary: {summary}

Write ONLY the caption. No preamble, no quotes."""


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
    """Professional-tone fallback templates for Filipino professionals."""
    title = article["title"]
    templates = [
        f"Most high-performing professionals overlook this. 👀 {title}. "
        f"Your career depends on your output — and your output depends on your health. 💡 "
        f"Worth a read if you take your performance seriously.",

        f"The research is clear, and it affects every professional in a demanding career. 🧠 {title}. "
        f"Small evidence-based habits compound into significant long-term results. "
        f"Save this — your future self will thank you. 🌿",

        f"High earners who ignore this pay for it later — literally. ⚡ {title}. "
        f"Your skills took years to build. Protect the body and mind behind them. 💚 "
        f"Tag a colleague who needs to see this.",
    ]
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

    # URL is posted as first comment in fb_poster.py — not in caption
    return hook


if __name__ == "__main__":
    test_articles = [
        {
            "title":   "New Study: Sleep Deprivation Reduces Cognitive Performance by 30%",
            "summary": "Researchers found chronic sleep loss significantly impairs decision-making in professionals.",
            "url":     "https://example.com/article",
        },
        {
            "title":   "Daily 20-Minute Walk Reduces Heart Disease Risk by 35%",
            "summary": "Consistent moderate walking significantly lowers cardiovascular risk even in sedentary jobs.",
            "url":     "https://example.com/article2",
        },
    ]
    for a in test_articles:
        print(f"\n── {a['title'][:50]} ──")
        print(generate_hook(a))
