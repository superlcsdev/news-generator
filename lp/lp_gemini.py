"""
lp/lp_gemini.py
Gemini API caller for @lawrenceprecioussia.
Matches the exact pattern from hook_writer.py and ai_selector.py —
same gemini-2.5-flash model, same OpenRouter fallback, same dotenv loading.
"""

import os
import requests
from dotenv import load_dotenv
from brand_voice import SYSTEM_PROMPT

load_dotenv()

GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent?key={key}"
)


def call_gemini(user_message: str, temperature: float = 0.92, max_tokens: int = 400) -> str | None:
    """
    Call Gemini with the LP brand system prompt.
    Falls back to OpenRouter (mistral-7b) if Gemini fails.
    Returns raw text or None if both fail.
    """
    result = _try_gemini(user_message, temperature, max_tokens)
    if result:
        return result

    print("  ⚠️ Gemini failed — trying OpenRouter fallback...")
    result = _try_openrouter(user_message)
    if result:
        return result

    print("  ❌ Both Gemini and OpenRouter failed.")
    return None


def _try_gemini(user_message: str, temperature: float, max_tokens: int) -> str | None:
    if not GEMINI_API_KEY:
        return None
    try:
        resp = requests.post(
            GEMINI_URL.format(key=GEMINI_API_KEY),
            json={
                "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": [{"parts": [{"text": user_message}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                    "topP": 0.95,
                },
            },
            timeout=30,
        )
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"  ⚠️ Gemini error: {e}")
        return None


def _try_openrouter(user_message: str) -> str | None:
    if not OPENROUTER_API_KEY:
        return None
    try:
        # Prepend system prompt manually since OpenRouter uses messages format
        full_prompt = f"{SYSTEM_PROMPT}\n\n---\n\n{user_message}"
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "mistralai/mistral-7b-instruct:free",
                "messages": [{"role": "user", "content": full_prompt}],
            },
            timeout=30,
        )
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"  ⚠️ OpenRouter error: {e}")
        return None
