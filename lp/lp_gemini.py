"""
lp/lp_gemini.py
Gemini API caller for @lawrenceprecioussia.

Uses gemini-2.5-flash-lite — free tier, thinking OFF by default,
optimized for structured output tasks (polls, post formatting).

Root cause of previous truncation: gemini-2.5-flash has thinking ON
by default and thinking tokens count against maxOutputTokens, eating
the budget before output is generated. Flash-Lite avoids this entirely.

Fallback: OpenRouter (mistral-7b-instruct:free)
"""

import os
import requests
from dotenv import load_dotenv
from brand_voice import SYSTEM_PROMPT

load_dotenv()

GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# gemini-2.5-flash-lite: free tier, thinking OFF by default, fast, reliable
# thinkingBudget:0 added as an explicit safety net in every call
GEMINI_MODEL = "gemini-2.5-flash-lite"
GEMINI_URL   = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent?key={{key}}"
)


def call_gemini(user_message: str, temperature: float = 0.92, max_tokens: int = 500) -> str | None:
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
                    # Explicitly disable thinking — prevents thinking tokens
                    # consuming the output budget on 2.5 models
                    "thinkingConfig": {"thinkingBudget": 0},
                },
            },
            timeout=30,
        )
        data = resp.json()

        # Surface API errors clearly in logs
        if "error" in data:
            print(f"  ⚠️ Gemini API error: {data['error'].get('message', data['error'])}")
            return None

        candidates = data.get("candidates", [])
        if not candidates:
            print(f"  ⚠️ Gemini returned no candidates. finishReason may be MAX_TOKENS.")
            print(f"  ⚠️ Full response: {data}")
            return None

        # Check finish reason — MAX_TOKENS means output was cut off
        finish_reason = candidates[0].get("finishReason", "")
        if finish_reason == "MAX_TOKENS":
            print(f"  ⚠️ Gemini hit MAX_TOKENS limit — response may be incomplete.")

        text = candidates[0]["content"]["parts"][0]["text"].strip()
        return text if text else None

    except Exception as e:
        print(f"  ⚠️ Gemini error: {e}")
        return None


def _try_openrouter(user_message: str) -> str | None:
    if not OPENROUTER_API_KEY:
        return None
    try:
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
