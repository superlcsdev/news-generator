"""
lp/lp_faith_generator.py
Generates Sunday morning Bible/faith posts for @lawrenceprecioussia.

Tone: Short verse + 1-2 lines of personal reflection.
      Learning-focused. Doctrinally safe for Church of Christ.
      Connects to journey only when it fits naturally.

Schedule: Sunday 7:00 AM SGT (11:00 PM Saturday UTC)
"""

import os
import re
import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# ─────────────────────────────────────────────────────────────────────────────
# DOCTRINAL SAFETY RULES
# ─────────────────────────────────────────────────────────────────────────────

DOCTRINAL_RULES = """DOCTRINAL SAFETY — strictly follow these rules:
- Use only Bible verses (NIV, ESV, NKJV, or KJV translations)
- Focus ONLY on universal Christian themes: faith, perseverance, love, wisdom,
  humility, gratitude, family, courage, trust in God, patience, service
- NEVER reference: Trinity doctrine by name, speaking in tongues, faith healing,
  denominational names, Virgin Mary, saints intercession, purgatory,
  prosperity gospel, or any theologically contested topic
- NEVER quote the Apocrypha or deuterocanonical books
- Keep commentary personal and reflective — not theological
- The reflection must be something any sincere Christian can agree with"""

# ─────────────────────────────────────────────────────────────────────────────
# WEEKLY THEME ROTATION — 13 themes, cycles 4x per year
# ─────────────────────────────────────────────────────────────────────────────

WEEKLY_THEMES = [
    {"theme": "perseverance through difficulty",       "context": "when life feels hard and progress is slow"},
    {"theme": "trusting God's timing",                 "context": "when things don't happen on our schedule"},
    {"theme": "the value of small beginnings",         "context": "when you feel like you're starting from nothing"},
    {"theme": "courage to step into the unknown",      "context": "when fear holds us back from taking a step"},
    {"theme": "gratitude for what we already have",    "context": "when we focus too much on what's missing"},
    {"theme": "wisdom in making decisions",            "context": "when we face choices that matter"},
    {"theme": "the strength found in community",       "context": "when we try to do everything alone"},
    {"theme": "patience as a form of faith",           "context": "when waiting feels like losing"},
    {"theme": "love as the foundation of everything",  "context": "in marriage, family, and relationships"},
    {"theme": "humility as strength, not weakness",    "context": "when pride gets in the way"},
    {"theme": "finding peace in uncertain times",      "context": "when anxiety about the future creeps in"},
    {"theme": "the power of consistent small actions", "context": "when big results feel far away"},
    {"theme": "rest and trusting God with the outcome","context": "when we carry too much on our own"},
]

# ─────────────────────────────────────────────────────────────────────────────
# JOURNEY MOMENTS — for optional natural connections
# ─────────────────────────────────────────────────────────────────────────────

JOURNEY_MOMENTS = [
    "the night we almost gave up after losing $600 of products on a restaurant table at 1am",
    "paying $20,000 to walk away from a stable job and an NUS university place",
    "our first presentation when we both stuttered and had no idea what we were doing",
    "a friend who disappeared without a word when he found out we started something",
    "8 years in a career Lawrence loved — and still choosing to leave",
    "the exhaustion of building something while both working full-time jobs",
    "trusting the process through months when nothing seemed to be working",
    "learning our different personalities were a strength, not a problem",
    "the moment we realized the business had grown beyond just the two of us",
    "Precious choosing to leave her career and her NUS studies on the same day",
]

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────────────────────────────────────

FAITH_SYSTEM_PROMPT = (
    "You are writing a Sunday morning Facebook post for Lawrence and Precious "
    "a husband-and-wife couple in Singapore sharing their Christian faith with their Filipino audience.\n\n"
    "AUDIENCE: Educated Filipino Christians in Singapore and the Philippines, aged 25-45.\n\n"
    "TONE:\n"
    "- Warm, sincere, humble. Like a friend sharing something from their quiet time.\n"
    "- Never preachy, never lecturing, never theological debate.\n"
    "- The reflection feels like a personal thought, not a sermon.\n"
    "- Short sentences. Conversational. Human.\n"
    "- Always 'we' not 'I' — this is a couple sharing together.\n\n"
    "POST STRUCTURE:\n"
    "Line 1: The Bible verse with reference (Book Chapter:Verse)\n"
    "Lines 2-3: 1-2 sentences of personal reflection — what this verse means to them today\n"
    "Optional: A gentle question for the audience\n\n"
    "LANGUAGE: English. One optional Taglish phrase in the CAPTION only.\n"
    "Caption examples: Magandang umaga. / Salamat sa biyaya. / Para sa inyong Linggo. / Pananatag ng puso.\n\n"
    "LENGTH: Maximum 5 lines total. Short. Let the verse breathe.\n\n"
    + DOCTRINAL_RULES
)

# ─────────────────────────────────────────────────────────────────────────────
# FORBIDDEN — doctrinal safety scan
# ─────────────────────────────────────────────────────────────────────────────

FAITH_FORBIDDEN = [
    "trinity", "holy trinity", "three in one", "speaking in tongues",
    "gift of tongues", "faith healing", "prosperity gospel",
    "name it claim it", "virgin mary", "mother mary", "hail mary",
    "purgatory", "papal", "denominational", "apocrypha", "deuterocanonical",
]

# ─────────────────────────────────────────────────────────────────────────────
# PRE-WRITTEN FALLBACK BANK — doctrinally verified
# ─────────────────────────────────────────────────────────────────────────────

FAITH_FALLBACKS = [
    {
        "post": (
            '"For I know the plans I have for you," declares the Lord, '
            '"plans to prosper you and not to harm you, plans to give you hope and a future." '
            "— Jeremiah 29:11\n\n"
            "We have held onto this verse during the seasons when nothing seemed to be moving. "
            "The silence was never the end of the story."
        ),
        "caption": "Magandang umaga.",
        "verse": "Jeremiah 29:11",
    },
    {
        "post": (
            '"Trust in the Lord with all your heart and lean not on your own understanding; '
            'in all your ways submit to him, and he will make your paths straight." — Proverbs 3:5-6\n\n'
            "Some decisions we made did not make sense to anyone around us at the time. "
            "This was the verse we kept coming back to."
        ),
        "caption": "Salamat sa biyaya.",
        "verse": "Proverbs 3:5-6",
    },
    {
        "post": (
            '"And let us not grow weary of doing good, for in due season we will reap, '
            'if we do not give up." — Galatians 6:9\n\n'
            "There were nights we wanted to stop. "
            "This verse kept us going one more day. "
            "Sometimes one more day is all it takes."
        ),
        "caption": "Huwag susuko.",
        "verse": "Galatians 6:9",
    },
    {
        "post": (
            '"Commit your work to the Lord, and your plans will be established." — Proverbs 16:3\n\n'
            "We have made a lot of plans over the years. "
            "The ones we gave to God first always turned out better than the ones we held too tightly."
        ),
        "caption": "Blessed Sunday.",
        "verse": "Proverbs 16:3",
    },
    {
        "post": (
            '"Two are better than one, because they have a good return for their labor: '
            'if either of them falls down, one can help the other up." — Ecclesiastes 4:9-10\n\n'
            "We did not fully understand this verse until we tried doing things separately. "
            "Together has always been better."
        ),
        "caption": "Pananatag ng puso.",
        "verse": "Ecclesiastes 4:9-10",
    },
    {
        "post": (
            '"Do not be anxious about anything, but in every situation, by prayer and petition, '
            'with thanksgiving, present your requests to God." — Philippians 4:6\n\n'
            "Easier said than done. But we have learned that starting with gratitude "
            "changes everything about how the rest of the day goes."
        ),
        "caption": "Para sa inyong Linggo.",
        "verse": "Philippians 4:6",
    },
    {
        "post": (
            '"She is clothed with strength and dignity, and she laughs without fear of the future." '
            "— Proverbs 31:25\n\n"
            "This one is for Precious — and for every woman who keeps showing up "
            "even when nobody sees how much it takes."
        ),
        "caption": "For the strong ones.",
        "verse": "Proverbs 31:25",
    },
    {
        "post": (
            '"Have I not commanded you? Be strong and courageous. Do not be afraid; '
            'do not be discouraged, for the Lord your God will be with you wherever you go." '
            "— Joshua 1:9\n\n"
            "Fear is not the absence of faith. "
            "Sometimes it is the very thing faith has to walk through."
        ),
        "caption": "Magandang umaga.",
        "verse": "Joshua 1:9",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _parse(raw: str, field: str, stop: str = None) -> str:
    pattern = (
        rf"{field}:\s*(.+?)(?={stop}:|$)"
        if stop else rf"{field}:\s*(.+?)$"
    )
    m = re.search(pattern, raw, re.DOTALL | re.IGNORECASE)
    return m.group(1).strip().strip('"').strip("\u201c").strip("\u201d") if m else ""


def _faith_safety_check(post: str) -> tuple:
    text = post.lower()
    for term in FAITH_FORBIDDEN:
        if term in text:
            return False, f"Doctrinally sensitive term: '{term}'"
    return True, ""


def _get_fallback() -> dict:
    week = datetime.date.today().isocalendar()[1]
    return FAITH_FALLBACKS[week % len(FAITH_FALLBACKS)]


def _should_connect_to_journey() -> bool:
    week = datetime.date.today().isocalendar()[1]
    return week % 3 == 0


# ─────────────────────────────────────────────────────────────────────────────
# GEMINI / OPENROUTER CALLERS
# ─────────────────────────────────────────────────────────────────────────────

def _call_gemini(prompt: str) -> str | None:
    if not GEMINI_API_KEY:
        return None
    try:
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}",
            json={
                "system_instruction": {"parts": [{"text": FAITH_SYSTEM_PROMPT}]},
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.80, "maxOutputTokens": 300, "topP": 0.90},
            },
            timeout=30,
        )
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"  Warning: Gemini faith error: {e}")
        return None


def _call_openrouter(prompt: str) -> str | None:
    if not OPENROUTER_API_KEY:
        return None
    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"},
            json={"model": "mistralai/mistral-7b-instruct:free",
                  "messages": [{"role": "user", "content": FAITH_SYSTEM_PROMPT + "\n\n---\n\n" + prompt}]},
            timeout=30,
        )
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"  Warning: OpenRouter faith error: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# MAIN GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

def generate_faith_post() -> dict:
    """
    Generate a Sunday Bible post.
    Returns: {post, caption, verse, theme}
    Falls back to pre-written bank if AI fails or safety check fails.
    """
    week        = datetime.date.today().isocalendar()[1]
    theme_data  = WEEKLY_THEMES[week % len(WEEKLY_THEMES)]
    theme       = theme_data["theme"]
    context     = theme_data["context"]

    journey_instruction = ""
    if _should_connect_to_journey():
        moment = JOURNEY_MOMENTS[week % len(JOURNEY_MOMENTS)]
        journey_instruction = (
            f"\nOPTIONAL: If it fits the verse naturally, you may briefly connect to this "
            f"real moment from our story: '{moment}'. "
            f"Only include if truly organic. If it feels forced, ignore this entirely."
        )

    user_msg = (
        f"Write a Sunday morning Bible post for @lawrenceprecioussia.\n\n"
        f"This week's theme: {theme}\n"
        f"Context: {context}"
        f"{journey_instruction}\n\n"
        f"Instructions:\n"
        f"- Choose a verse that genuinely speaks to this theme\n"
        f"- Write 1-2 lines of sincere personal reflection\n"
        f"- Maximum 5 lines total\n"
        f"- Doctrinal safety rules apply strictly\n\n"
        f"Output format (exactly):\n"
        f"POST: [verse + reflection]\n"
        f"CAPTION: [2-6 words]\n"
        f"VERSE: [Book Chapter:Verse]"
    )

    raw = _call_gemini(user_msg) or _call_openrouter(user_msg)

    if raw:
        print(f"\n--- Gemini raw (faith) ---\n{raw}\n---")
        post    = _parse(raw, "POST", "CAPTION")
        caption = _parse(raw, "CAPTION", "VERSE")
        verse   = _parse(raw, "VERSE")

        safe, reason = _faith_safety_check(post)
        if not safe:
            print(f"  Warning: Faith safety check failed ({reason}). Using fallback.")
            fallback = _get_fallback()
            fallback["theme"] = theme
            return fallback

        return {"post": post, "caption": caption, "verse": verse, "theme": theme}

    print("  Warning: AI unavailable. Using pre-written faith fallback.")
    fallback = _get_fallback()
    fallback["theme"] = theme
    return fallback


if __name__ == "__main__":
    result = generate_faith_post()
    print(f"\nTheme:   {result['theme']}")
    print(f"Verse:   {result.get('verse', 'N/A')}")
    print(f"Caption: {result['caption']}")
    print(f"\nPost:\n{result['post']}")
