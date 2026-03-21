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

HOOK_PROMPT = """You are writing a Facebook post caption for Filipino professionals — nurses, 
IT workers, engineers, architects, pharmacists — based in Singapore and the Philippines.

Write a caption for this health article that sounds like a real person wrote it, not AI.

LANGUAGE RULES — very important:
- Use simple, everyday English. Short sentences. Max 15 words per sentence.
- Write like you're messaging a smart friend — casual but not sloppy
- Contractions always: "you're" not "you are", "it's" not "it is", "don't" not "do not"
- Be specific: "nurses on 12-hour shifts" not "busy professionals"
- NEVER use these words: leverage, optimise, empower, unlock, holistic, sustainable,
  transformative, actionable, synergy, catalyse, utilise, impactful, robust, comprehensive
- Never start with "Are you..." or "Did you know..." — too generic, sounds like AI
- One idea per sentence. If a sentence is over 15 words, break it into two.
- Very occasional Filipino word for warmth (max 1 per post, only if it fits naturally)
  e.g. "Kaya mo ito." — never heavy Taglish

CONTENT RULES:
- Speak to their professional life — health as career fuel, not just wellness
- No hardship framing. No OFW struggle. No remittance mentions.
- A surprising fact or a sharp honest observation works better than motivation

Structure:
- Line 1: One strong opening line. No emoji here. Not a question. Something that makes them stop scrolling.
- Lines 2–3: Two short sentences adding context. Keep it grounded and real.
- Last line: Short CTA. Something a real person would actually say.

Use 2–3 emojis. Max 4 sentences total. Don't mention the source website.

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
    """Simple, human-sounding fallback templates for Filipino professionals."""
    title = article["title"]
    templates = [
        f"Most professionals ignore this until it's too late. 👀\n"
        f"{title}.\n"
        f"Your body keeps the score — especially after years of long shifts and late nights. 💡\n"
        f"Save this. Read it when you have 2 minutes.",

        f"This one's for anyone working long hours and wondering why they're always tired. 🧠\n"
        f"{title}.\n"
        f"Small habits compound. The ones you skip do too. 🌿\n"
        f"Tag a colleague who needs to see this.",

        f"High performers miss this more than anyone else. ⚡\n"
        f"{title}.\n"
        f"Your skills are only as good as the person carrying them. Take care of that person. 💚\n"
        f"Worth reading — drop a comment if this hits close to home.",
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
