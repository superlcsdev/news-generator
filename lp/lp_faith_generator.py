"""
lp/lp_faith_generator.py
Generates Sunday morning Bible/faith posts for @lawrenceprecioussia.

Image card: NKJV Bible verse only — clean, just verse text + reference
Facebook caption: Personal reflection + practical lesson audience can apply

Verse categories: leadership, success attitude, couple relationship,
                  financial literacy, health

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
# DOCTRINAL SAFETY
# ─────────────────────────────────────────────────────────────────────────────

DOCTRINAL_RULES = """DOCTRINAL SAFETY — strictly follow:
- NKJV translation only
- Universal Christian themes only: faith, perseverance, wisdom, love,
  humility, gratitude, family, courage, trust in God, patience
- NEVER reference: Trinity by name, speaking in tongues, faith healing,
  denominational names, Virgin Mary, saints intercession, purgatory,
  prosperity gospel, or any contested doctrine
- NEVER quote Apocrypha or deuterocanonical books
- Reflection must be something any sincere Christian can agree with"""

# ─────────────────────────────────────────────────────────────────────────────
# VERSE CATEGORIES — 5 themes rotating weekly
# ─────────────────────────────────────────────────────────────────────────────

VERSE_CATEGORIES = [
    {
        "category": "leadership",
        "context": "leading others well, serving with integrity, making wise decisions for the team",
        "sample_verses": ["Joshua 1:9", "Proverbs 11:14", "Mark 10:43-44", "1 Timothy 4:12"],
    },
    {
        "category": "success attitude",
        "context": "perseverance, working with excellence, not giving up, doing things with purpose",
        "sample_verses": ["Galatians 6:9", "Colossians 3:23", "Philippians 4:13", "Proverbs 16:3"],
    },
    {
        "category": "couple relationship",
        "context": "marriage, partnership, supporting each other, building a life together in faith",
        "sample_verses": ["Ecclesiastes 4:9-10", "Proverbs 31:10-11", "1 Corinthians 13:4-7", "Genesis 2:24"],
    },
    {
        "category": "financial literacy",
        "context": "stewardship of money, wisdom in finances, generosity, not loving money above all",
        "sample_verses": ["Proverbs 21:5", "Luke 16:10", "Malachi 3:10", "Proverbs 13:11"],
    },
    {
        "category": "health",
        "context": "taking care of the body, rest, wholeness of mind and spirit, God's temple",
        "sample_verses": ["1 Corinthians 6:19-20", "3 John 1:2", "Psalm 23:2-3", "Isaiah 40:31"],
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────────────────────────────────────

FAITH_SYSTEM_PROMPT = (
    "You are writing a Sunday morning Facebook post for Lawrence and Precious — "
    "a husband-and-wife couple in Singapore sharing their Christian faith with their Filipino audience.\n\n"
    "AUDIENCE: Educated Filipino Christians in Singapore and the Philippines, aged 25-45.\n\n"
    "TONE:\n"
    "- Warm, sincere, humble. Like a friend sharing from their quiet time.\n"
    "- Never preachy, never lecturing.\n"
    "- Reflection feels personal, not a sermon.\n"
    "- Short sentences. Conversational. Human.\n"
    "- Always 'we' not 'I'.\n\n"
    "STRUCTURE:\n"
    "VERSE field: ONLY the exact Bible verse text in NKJV + reference. Nothing else.\n"
    "POST field: 3-5 sentences of personal reflection + 1 practical lesson the audience can apply today.\n"
    "            End with a gentle question.\n"
    "CAPTION field: 2-5 words Taglish reaction.\n\n"
    + DOCTRINAL_RULES
)

# ─────────────────────────────────────────────────────────────────────────────
# FALLBACK BANK — doctrinally verified, split into verse + post + caption
# ─────────────────────────────────────────────────────────────────────────────

FAITH_FALLBACKS = [
    {
        "category": "leadership",
        "verse_text": '"Have I not commanded you? Be strong and courageous. Do not be afraid; do not be discouraged, for the Lord your God will be with you wherever you go." — Joshua 1:9 (NKJV)',
        "post": (
            "Leadership isn't the absence of fear — it's moving forward while afraid. "
            "We have made decisions that terrified us. Resigned from jobs, walked away from security, "
            "chosen people over comfort. Each time, this verse was what we came back to. "
            "The practical lesson we've learned: courage isn't a feeling. It's a decision you make before the feeling arrives. "
            "What's one decision you've been putting off that actually just needs courage, not more preparation?"
        ),
        "caption": "Maging matapang.",
        "verse": "Joshua 1:9",
    },
    {
        "category": "success attitude",
        "verse_text": '"And let us not grow weary while doing good, for in due season we shall reap if we do not lose heart." — Galatians 6:9 (NKJV)',
        "post": (
            "There were seasons when we did the right things and saw no results. "
            "Showed up, worked quietly, kept going — and nothing seemed to move. "
            "This verse didn't promise speed. It promised a harvest. "
            "The lesson we carry: the gap between sowing and reaping is not wasted time — it is growing time. "
            "What good thing are you still doing even when results are slow?"
        ),
        "caption": "Huwag susuko.",
        "verse": "Galatians 6:9",
    },
    {
        "category": "couple relationship",
        "verse_text": '"Two are better than one, because they have a good reward for their labor. For if they fall, one will lift up his companion." — Ecclesiastes 4:9-10 (NKJV)',
        "post": (
            "We learned this verse not by reading it, but by living it. "
            "There were low moments — seasons of doubt, exhaustion, and wanting to stop. "
            "The only reason we kept going was because one of us was always standing when the other wasn't. "
            "The practical lesson: your partner is not just your companion — they are your strategy. "
            "How are you and your partner carrying each other through the heavy seasons right now?"
        ),
        "caption": "Mas malakas tayo.",
        "verse": "Ecclesiastes 4:9-10",
    },
    {
        "category": "financial literacy",
        "verse_text": '"The plans of the diligent lead surely to plenty, but those of everyone who is hasty, surely to poverty." — Proverbs 21:5 (NKJV)',
        "post": (
            "We used to make financial decisions based on how we felt in the moment. "
            "Impulse. Emotion. FOMO. And we paid for it — literally. "
            "This verse changed how we look at money: diligence means having a plan and sticking to it even when it's boring. "
            "The practical lesson: the most powerful financial move isn't the biggest one — it's the consistent one, made slowly and deliberately. "
            "What's one financial habit you want to be more diligent about this week?"
        ),
        "caption": "Mag-isip muna.",
        "verse": "Proverbs 21:5",
    },
    {
        "category": "health",
        "verse_text": '"Or do you not know that your body is the temple of the Holy Spirit who is in you, whom you have from God, and you are not your own?" — 1 Corinthians 6:19 (NKJV)',
        "post": (
            "For years we treated rest as laziness and busyness as a badge of honour. "
            "We built things while running on empty — and eventually the body always sends the bill. "
            "This verse reframed everything: taking care of our health isn't selfish, it's stewardship. "
            "The practical lesson: you cannot pour from an empty cup, and you cannot build anything lasting on a broken foundation. "
            "What's one thing you've been neglecting about your health that deserves attention this week?"
        ),
        "caption": "Alagaan ang sarili.",
        "verse": "1 Corinthians 6:19",
    },
    {
        "category": "success attitude",
        "verse_text": '"And whatever you do, do it heartily, as to the Lord and not to men." — Colossians 3:23 (NKJV)',
        "post": (
            "We've had jobs where the boss wasn't watching, where no one would notice if we gave 60%. "
            "This verse changed the standard we worked to. "
            "Not for the salary. Not for the recognition. For something higher. "
            "The practical lesson: excellence isn't about the audience — it's about who you're becoming through the work. "
            "What would change about how you worked this week if you truly believed God was watching?"
        ),
        "caption": "Buong puso.",
        "verse": "Colossians 3:23",
    },
    {
        "category": "leadership",
        "verse_text": '"But whoever desires to become great among you, let him be your servant." — Mark 10:43 (NKJV)',
        "post": (
            "The leadership model the world teaches is very different from this one. "
            "We used to think leading meant being in front. We learned it means staying behind long enough to make sure everyone else moves forward. "
            "The people we've seen lead well are always the ones who give more credit than they take. "
            "The practical lesson: the fastest way to grow your influence is to invest in someone else's growth today. "
            "Who is one person in your life you could serve better this week?"
        ),
        "caption": "Paglilingkod ang pamumuno.",
        "verse": "Mark 10:43",
    },
    {
        "category": "health",
        "verse_text": '"He makes me to lie down in green pastures; He leads me beside the still waters. He restores my soul." — Psalm 23:2-3 (NKJV)',
        "post": (
            "Rest was the hardest discipline we had to learn. "
            "We confused stillness with falling behind. We confused rest with weakness. "
            "But God doesn't command rest as a reward for finishing — He commands it as a rhythm for living. "
            "The practical lesson: a soul that is never restored eventually has nothing left to give. "
            "When did you last truly rest — not just stop working, but actually let your soul be still?"
        ),
        "caption": "Pahinga muna.",
        "verse": "Psalm 23:2-3",
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


def _faith_safety_check(text: str) -> tuple:
    forbidden = [
        "trinity", "holy trinity", "three in one", "speaking in tongues",
        "gift of tongues", "faith healing", "prosperity gospel",
        "name it claim it", "virgin mary", "mother mary", "hail mary",
        "purgatory", "papal", "denominational", "apocrypha",
    ]
    lower = text.lower()
    for term in forbidden:
        if term in lower:
            return False, f"Doctrinally sensitive: '{term}'"
    return True, ""


def _get_fallback(category: str = None) -> dict:
    week = datetime.date.today().isocalendar()[1]
    if category:
        matches = [f for f in FAITH_FALLBACKS if f["category"] == category]
        if matches:
            return matches[week % len(matches)]
    return FAITH_FALLBACKS[week % len(FAITH_FALLBACKS)]


# ─────────────────────────────────────────────────────────────────────────────
# GEMINI / OPENROUTER CALLERS
# ─────────────────────────────────────────────────────────────────────────────

def _call_gemini(prompt: str) -> str | None:
    if not GEMINI_API_KEY:
        return None
    try:
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}",
            json={
                "system_instruction": {"parts": [{"text": FAITH_SYSTEM_PROMPT}]},
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.80,
                    "maxOutputTokens": 600,
                    "topP": 0.90,
                    "thinkingConfig": {"thinkingBudget": 0},
                },
            },
            timeout=30,
        )
        data = resp.json()
        if "error" in data:
            print(f"  Warning: Gemini faith error: {data['error'].get('message', '')}")
            return None
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"  Warning: Gemini faith error: {e}")
        return None


def _call_openrouter(prompt: str) -> str | None:
    if not OPENROUTER_API_KEY:
        return None
    full_prompt = FAITH_SYSTEM_PROMPT + "\n\n---\n\n" + prompt
    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"},
            json={"model": "openrouter/free", "messages": [{"role": "user", "content": full_prompt}]},
            timeout=30,
        )
        data = resp.json()
        if "error" in data:
            print(f"  Warning: OpenRouter error: {data['error'].get('message', '')}")
            return None
        choices = data.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "").strip()
    except Exception as e:
        print(f"  Warning: OpenRouter faith error: {e}")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# MAIN GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

def generate_faith_post() -> dict:
    """
    Generate a Sunday Bible post.
    Returns: {verse_text, post, caption, verse, category}
      verse_text → shown on image card (verse only, NKJV)
      post       → shown in Facebook caption (reflection + lesson)
      caption    → 2-5 word Taglish above the FB caption
    """
    week     = datetime.date.today().isocalendar()[1]
    cat_data = VERSE_CATEGORIES[week % len(VERSE_CATEGORIES)]
    category = cat_data["category"]
    context  = cat_data["context"]
    samples  = ", ".join(cat_data["sample_verses"])

    user_msg = (
        f"Write a Sunday morning Bible post for @lawrenceprecioussia.\n\n"
        f"Category: {category}\n"
        f"Context: {context}\n"
        f"Sample verses for reference (you may use one of these or another NKJV verse that fits better): {samples}\n\n"
        f"Requirements:\n"
        f"- NKJV translation only\n"
        f"- VERSE field: exact verse text in quotes + reference. Nothing else.\n"
        f"- POST field: 3-5 sentences personal reflection + 1 practical lesson + 1 gentle question\n"
        f"- CAPTION field: 2-5 word Taglish reaction\n"
        f"- Doctrinal safety rules apply strictly\n\n"
        f"Output format (exactly):\n"
        f"VERSE: [exact NKJV verse text in quotes — reference at end e.g. — Proverbs 3:5 (NKJV)]\n"
        f"POST: [reflection + lesson + question]\n"
        f"CAPTION: [2-5 words Taglish]"
    )

    raw = _call_gemini(user_msg) or _call_openrouter(user_msg)

    if raw:
        print(f"\n--- Gemini raw (faith) ---\n{raw}\n---")
        verse_text = _parse(raw, "VERSE", "POST")
        post       = _parse(raw, "POST",  "CAPTION")
        caption    = _parse(raw, "CAPTION")

        # Extract verse reference from verse_text for logging
        verse_ref = ""
        m = re.search(r"—\s*(.+?)\s*\(NKJV\)", verse_text)
        if m:
            verse_ref = m.group(1).strip()

        safe, reason = _faith_safety_check(verse_text + " " + post)
        if not safe:
            print(f"  Warning: Faith safety check failed ({reason}). Using fallback.")
            fb = _get_fallback(category)
            fb["category"] = category
            return fb

        if not verse_text or not post:
            print("  Warning: Incomplete faith response. Using fallback.")
            fb = _get_fallback(category)
            fb["category"] = category
            return fb

        return {
            "verse_text": verse_text,
            "post":       post,
            "caption":    caption,
            "verse":      verse_ref,
            "category":   category,
        }

    print("  Warning: AI unavailable. Using pre-written faith fallback.")
    fb = _get_fallback(category)
    fb["category"] = category
    return fb


if __name__ == "__main__":
    result = generate_faith_post()
    print(f"\nCategory: {result['category']}")
    print(f"Verse ref: {result.get('verse', 'N/A')}")
    print(f"Caption:   {result['caption']}")
    print(f"\nVERSE (image):\n{result['verse_text']}")
    print(f"\nPOST (caption):\n{result['post']}")
