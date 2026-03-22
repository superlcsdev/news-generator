"""
lp/lp_post_generator.py
Generates all post types for @lawrenceprecioussia.
Mirrors hook_writer.py pattern — one module, clean functions per type.

Post types:
  generate_text_post()  — Formats A / B / BW / C / D / E
  generate_poll_post()  — Engagement poll with emoji options
  generate_news_hook()  — Reframes a news article through couple brand lens
  get_cta_post()        — Rotating pre-written CTA (no Gemini needed)
"""

import re
import random
import datetime
from brand_voice import FORMATS, FORMAT_WEIGHTS, HOOKS, HOOK_WEIGHTS
from lp_gemini import call_gemini
from story_bank import get_seed_context


# ─────────────────────────────────────────────────────────────────────────────
# SAFETY FILTER — hard block on forbidden words/phrases
# Runs on every generated post BEFORE it is returned or published
# ─────────────────────────────────────────────────────────────────────────────

FORBIDDEN_TERMS = [
    # Brand / business identity
    "usana", "mlm", "multi-level", "multilevel", "network marketing",
    "direct selling", "direct sales", "direct sell",
    # Recruitment language
    "business opportunity", "income opportunity", "join our team",
    "join us", "be your own boss", "work from home opportunity",
    "downline", "upline", "brand partner", "distributor",
    "associate program", "sign up with us",
    # Product / health claims
    "supplement", "vitamin", "nutritional", "health product",
    "weight loss", "immune system boost",
    # Rank / income reveals
    "gold director", "diamond director", "uem",
    "commission", "rank advancement", "rank qualification",
    # Pitch phrases
    "message us to", "dm us", "send us a message to learn",
    "comment to join", "link in bio for",
]


def _safety_check(post: str, caption: str) -> tuple[bool, str]:
    """
    Returns (is_safe, reason).
    Checks post + caption for forbidden terms and brand voice violations.
    """
    combined = (post + " " + caption).lower()

    # Forbidden business/product terms
    for term in FORBIDDEN_TERMS:
        if term in combined:
            return False, f"Forbidden term detected: '{term}'"

    # Check for solo "I" or "My" pronoun as narrative subject — must always be "we/our"
    # Strip quoted speech first (e.g. "I said..." is okay inside dialogue)
    import re as _re
    post_no_quotes = _re.sub(r'"[^"]*"', '', post)
    post_no_quotes = _re.sub(r"'[^']*'", '', post_no_quotes)
    # Flag if "I" appears more than once OR "My" appears as a possessive narrator
    i_matches  = _re.findall(r'\bI\b', post_no_quotes)
    my_matches = _re.findall(r'\bMy\b', post_no_quotes)
    if len(i_matches) > 1:
        return False, f"Post uses 'I' {len(i_matches)} times — must speak as a couple using 'we'"
    if len(my_matches) > 0:
        return False, f"Post uses 'My' — must use 'our' to speak as a couple"

    return True, ""


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _weighted_choice(weights: dict) -> str:
    keys = list(weights.keys())
    vals = list(weights.values())
    return random.choices(keys, weights=vals, k=1)[0]


def _clean(text: str) -> str:
    return text.strip().strip('"').strip('\u201c').strip('\u201d').strip()


def _parse(raw: str, field: str, stop: str = None) -> str:
    pattern = (
        rf"{field}:\s*(.+?)(?={stop}:|$)"
        if stop else
        rf"{field}:\s*(.+?)$"
    )
    m = re.search(pattern, raw, re.DOTALL | re.IGNORECASE)
    return _clean(m.group(1)) if m else ""


# ─────────────────────────────────────────────────────────────────────────────
# 1. TEXT POST — Formats A / B / BW / C / D / E
# ─────────────────────────────────────────────────────────────────────────────

def generate_text_post(post_format: str = "any", hook: str = "any") -> dict:
    """
    Generate one on-brand text post.
    Returns: {post, caption, format, hook}
    Falls back to template if Gemini unavailable.
    """
    fmt  = post_format if post_format in FORMAT_WEIGHTS else _weighted_choice(FORMAT_WEIGHTS)
    hook = hook if hook in HOOK_WEIGHTS else _weighted_choice(HOOK_WEIGHTS)

    # Inject a real story seed for B, BW, D formats
    story_context = ""
    if fmt in ("B", "BW", "D", "A"):
        story_context = get_seed_context(fmt)

    # Format-specific extra rules
    format_extra = ""
    if fmt == "B":
        format_extra = (
            "CRITICAL FOR FORMAT B — READ CAREFULLY:\n"
            "- The couple tells the story TOGETHER from a shared 'we/our' perspective\n"
            "- NEVER use 'I' or 'My' — not even once\n"
            "- NEVER write 'My voice...' or 'I watched...' — that is one person narrating\n"
            "- WRONG: 'My voice decided to go on vacation.' — solo narrator\n"
            "- WRONG: 'She was amazing. I was not.' — observer framing\n"
            "- RIGHT: 'Our voices both disappeared. The audience was very patient.'\n"
            "- RIGHT: 'We both panicked. She recovered faster. Of course.'\n"
            "- RIGHT: 'We couldn't get through a sentence. We still laugh about it.'\n"
            "- The humor comes from the COUPLE sharing the embarrassment together\n"
            "- Use 'we', 'our', 'us' throughout — every sentence\n"
            "- Caption: 2-5 words, reaction, often Taglish. Punchline is in the POST.\n\n"
        )
    elif fmt == "BW":
        format_extra = (
            "CRITICAL FOR FORMAT BW:\n"
            "- Start with a funny couple moment using 'we' — never 'I'\n"
            "- End with a quiet insight that reframes the moment\n"
            "- The laugh opens the door. The wisdom is what they save.\n"
            "- Both parts must speak as a couple — 'we realized', 'we learned', never 'I realized'\n\n"
        )

    user_msg = (
        f"Generate exactly 1 Facebook post for @lawrenceprecioussia.\n\n"
        f"FORMAT: {fmt} — {FORMATS[fmt]}\n"
        f"EMOTION HOOK: {hook}\n\n"
        + (f"{story_context}\n\n" if story_context else "")
        + format_extra
        + f"Strict rules:\n"
        f"- Always 'we' — never 'I' — this is a couple speaking together, not one person narrating\n"
        f"- English body only. Taglish allowed in CAPTION only.\n"
        f"- Zero product/business/opportunity mentions\n"
        f"- Max 4 sentences in POST body\n"
        f"- Short sentences — max 15 words each\n"
        f"- No exclamation marks more than once per post\n"
        f"- Never ask people to follow, like, or share\n"
        f"- Never use: leverage, empower, unlock, holistic, synergy, transformative\n"
        f"- Apply the Golden Test before finalising\n\n"
        f"Output format (use exactly):\n"
        f"POST: [post body]\n"
        f"CAPTION: [2–8 words]\n"
        f"FORMAT: [{fmt}]\n"
        f"HOOK: [{hook}]"
    )

    raw = call_gemini(user_msg, temperature=0.92)

    if raw:
        print(f"\n--- Gemini raw ---\n{raw}\n---")
        result = {
            "post":    _parse(raw, "POST", "CAPTION"),
            "caption": _parse(raw, "CAPTION", "FORMAT"),
            "format":  fmt,
            "hook":    hook,
        }
        # Safety filter — retry once if forbidden terms detected
        is_safe, reason = _safety_check(result["post"], result["caption"])
        if not is_safe:
            print(f"  ⚠️ Safety filter triggered: {reason}. Retrying...")
            raw2 = call_gemini(user_msg + "\n\nIMPORTANT: Do NOT mention any business, product, or opportunity. Keep it purely personal and relatable.", temperature=0.85)
            if raw2:
                result = {
                    "post":    _parse(raw2, "POST", "CAPTION"),
                    "caption": _parse(raw2, "CAPTION", "FORMAT"),
                    "format":  fmt,
                    "hook":    hook,
                }
                is_safe2, reason2 = _safety_check(result["post"], result["caption"])
                if not is_safe2:
                    print(f"  ⚠️ Retry also failed safety check: {reason2}. Using fallback.")
                    return _text_fallback(fmt, hook)
        return result

    # Fallback if both AI providers fail
    print("  ⚠️ Using template fallback for text post.")
    return _text_fallback(fmt, hook)


def _text_fallback(fmt: str, hook: str) -> dict:
    """Pre-written fallback posts per format — no AI needed."""
    fallbacks = {
        "A":  ("Two incomes. Two professionals. One budget that somehow still ran out before the 25th.",
               "Math wasn't mathing."),
        "B":  ("We were both too scared to quit our jobs. So we made a deal — whoever hit the goal first, "
               "the other would follow. Spoiler: she went first. Of course.",
               "Siyempre sya pa."),
        "BW": ("She asked me why I was still awake at midnight researching. I said I was just curious. "
               "Turns out, curiosity is where most things actually start.",
               "Just curious."),
        "C":  ("If you could design your ideal Monday morning — no alarm, no commute, no boss — "
               "what would it actually look like?",
               "We'll go first in the comments."),
        "D":  ("Nobody told us that building something part-time while working full-time would be exhausting. "
               "They also didn't tell us it would be worth it. Both things turned out to be true.",
               "Both."),
        "E":  ("One of the people we walked with told us she almost gave up three times. She didn't. "
               "Now she's the one telling other people not to give up. We didn't do that. She did.",
               "That's everything."),
    }
    post, caption = fallbacks.get(fmt, fallbacks["A"])
    return {"post": post, "caption": caption, "format": fmt, "hook": hook}


# ─────────────────────────────────────────────────────────────────────────────
# 2. POLL POST
# ─────────────────────────────────────────────────────────────────────────────

# Rotate topics by day so every poll feels fresh
POLL_TOPICS = [
    "what your typical weeknight looks like after work",
    "what you do right after receiving your salary",
    "who makes the big financial decisions in your household",
    "your ideal free Saturday with zero obligations",
    "how you really feel about your current work situation",
    "the thing couples argue about most without saying it out loud",
    "what you wish you had more of in your daily life",
    "which expense surprises you every single month",
    "how you feel about Mondays — honestly",
    "the colleague type that exists in every Filipino workplace",
]

POLL_FALLBACK = {
    "question": "What does your Friday evening actually look like?",
    "options": [
        "🅐  Already asleep by 9 PM. No shame.",
        "🅑  Doomscrolling until midnight somehow.",
        "🅒  Quietly planning how to escape the 9-to-5.",
        "🅓  What's rest? I have weekend errands.",
    ],
    "caption": "Be honest.",
    "fb_message": (
        "Be honest.\n\n"
        "What does your Friday evening actually look like?\n\n"
        "🅐  Already asleep by 9 PM. No shame.\n"
        "🅑  Doomscrolling until midnight somehow.\n"
        "🅒  Quietly planning how to escape the 9-to-5.\n"
        "🅓  What's rest? I have weekend errands.\n\n"
        "Comment your answer below 👇"
    ),
}


def generate_poll_post() -> dict:
    """
    Generate a poll-style post with 3-4 emoji options.
    Returns: {question, options, caption, fb_message}
    """
    day   = datetime.date.today().timetuple().tm_yday
    topic = POLL_TOPICS[day % len(POLL_TOPICS)]

    user_msg = (
        f"Generate a poll-style Facebook post for @lawrenceprecioussia.\n"
        f"Topic: {topic}\n\n"
        f"Rules:\n"
        f"- Question: fun, relatable, no wrong answers, complete sentence\n"
        f"- 4 short options (A, B, C, D) — funny or painfully relatable\n"
        f"- Each option: maximum 8 words, no punctuation at the end\n"
        f"- English throughout. Caption can be 1 Taglish phrase.\n"
        f"- Zero business/product/opportunity mentions\n\n"
        f"Output EXACTLY in this format, nothing else:\n"
        f"QUESTION: [complete question here]\n"
        f"A: [option text]\n"
        f"B: [option text]\n"
        f"C: [option text]\n"
        f"D: [option text]\n"
        f"CAPTION: [2-5 words]"
    )

    # Increased max_tokens to 400 — poll needs more room than a single post
    raw = call_gemini(user_msg, temperature=0.92, max_tokens=400)

    if not raw:
        print("  ⚠️ Gemini unavailable — using poll fallback.")
        return POLL_FALLBACK

    print(f"\n--- Gemini raw (poll) ---\n{raw}\n---")

    # Robust line-by-line parser — handles any whitespace/formatting variation
    question = ""
    opt_a = opt_b = opt_c = opt_d = ""
    caption = ""

    for line in raw.strip().splitlines():
        line = line.strip()
        if line.upper().startswith("QUESTION:"):
            question = line[9:].strip().strip('"')
        elif re.match(r"^A[\s:.]", line, re.IGNORECASE):
            opt_a = re.sub(r"^A[\s:.]+", "", line, flags=re.IGNORECASE).strip()
        elif re.match(r"^B[\s:.]", line, re.IGNORECASE):
            opt_b = re.sub(r"^B[\s:.]+", "", line, flags=re.IGNORECASE).strip()
        elif re.match(r"^C[\s:.]", line, re.IGNORECASE):
            opt_c = re.sub(r"^C[\s:.]+", "", line, flags=re.IGNORECASE).strip()
        elif re.match(r"^D[\s:.]", line, re.IGNORECASE):
            opt_d = re.sub(r"^D[\s:.]+", "", line, flags=re.IGNORECASE).strip()
        elif line.upper().startswith("CAPTION:"):
            caption = line[8:].strip().strip('"')

    # Validate — if question or any option is missing, use fallback
    missing = []
    if not question: missing.append("question")
    if not opt_a:    missing.append("option A")
    if not opt_b:    missing.append("option B")
    if not opt_c:    missing.append("option C")

    if missing:
        print(f"  ⚠️ Poll parse failed — missing: {', '.join(missing)}. Using fallback.")
        return POLL_FALLBACK

    # Use fallback caption if missing
    if not caption:
        caption = "Which one are you?"

    options = [
        f"🅐  {opt_a}",
        f"🅑  {opt_b}",
        f"🅒  {opt_c}",
    ]
    if opt_d:
        options.append(f"🅓  {opt_d}")

    fb_message = (
        f"{caption}\n\n"
        f"{question}\n\n"
        + "\n".join(options)
        + "\n\nComment your answer below 👇"
    )

    return {
        "question":   question,
        "options":    options,
        "caption":    caption,
        "fb_message": fb_message,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. NEWS HOOK — reframes a news article through the LP couple brand lens
# ─────────────────────────────────────────────────────────────────────────────

def generate_news_hook(article: dict) -> dict:
    """
    Reframe a news article through the Lawrence & Precious couple brand lens.
    article = {title, url, source, summary}
    Returns: {post, caption, article_url, format, hook}
    """
    user_msg = (
        f"A news article relevant to our Filipino audience has been published.\n\n"
        f"Article title: {article.get('title', '')}\n"
        f"Source: {article.get('source', '')}\n"
        f"Summary: {article.get('summary', article.get('title', ''))[:300]}\n\n"
        f"Write a Facebook post for @lawrenceprecioussia that:\n"
        f"1. Connects this news to the everyday reality of our Filipino audience\n"
        f"2. Uses our brand voice — 'we', relatable, honest, never a lecture\n"
        f"3. Makes them feel seen, not educated\n"
        f"4. Ends with a genuine open question inviting them to share their thoughts\n"
        f"5. NO product/business/opportunity mentions at all\n\n"
        f"Output format (use exactly):\n"
        f"POST: [post body — max 4 sentences + 1 question]\n"
        f"CAPTION: [2–8 words]"
    )

    raw = call_gemini(user_msg, temperature=0.88, max_tokens=350)

    if not raw:
        # Fallback: simple news hook template
        post = (
            f"This caught our attention today.\n\n"
            f"{article.get('title', '')}.\n\n"
            f"We've felt this reality ourselves — and we know many of you have too. "
            f"What's your take on this?"
        )
        return {
            "post": post, "caption": "Worth talking about.",
            "article_url": article.get("url", ""), "format": "NEWS", "hook": "PAIN",
        }

    print(f"\n--- Gemini raw (news) ---\n{raw}\n---")
    result = {
        "post":        _parse(raw, "POST", "CAPTION"),
        "caption":     _parse(raw, "CAPTION"),
        "article_url": article.get("url", ""),
        "format":      "NEWS",
        "hook":        "PAIN",
    }
    is_safe, reason = _safety_check(result["post"], result["caption"])
    if not is_safe:
        print(f"  ⚠️ News hook failed safety check: {reason}. Using fallback.")
        result["post"] = (
            f"This caught our attention.\n\n"
            f"{article.get('title', '')}.\n\n"
            f"We know a lot of you are feeling this too. What's your take?"
        )
        result["caption"] = "Worth talking about."
    return result


# ─────────────────────────────────────────────────────────────────────────────
# 4. CTA POST — pre-written rotating bank, no Gemini needed
# ─────────────────────────────────────────────────────────────────────────────

CTA_BANK = [
    {
        "caption": "We get asked this a lot.",
        "post": (
            "A lot of people have been asking us how we started — "
            "especially those juggling a full-time job while trying to build something on the side.\n\n"
            "We've been there. We know exactly what that feels like.\n\n"
            "If you're curious about our story and want to know where we began, "
            "comment START below and we'll walk you through it. "
            "No pressure, no pitch — just a real conversation."
        ),
    },
    {
        "caption": "If this is you, keep reading.",
        "post": (
            "You have a stable job. You're not struggling — but something feels missing.\n\n"
            "Maybe it's the feeling that your time isn't really yours. "
            "Or that one income isn't quite enough for the life you want for your family.\n\n"
            "We felt that too. Comment START below and we'll share where our story started."
        ),
    },
    {
        "caption": "Starting is the hardest part.",
        "post": (
            "We started with full-time jobs, zero business experience, "
            "and a lot of uncertainty. We didn't have it all figured out — we just began.\n\n"
            "If you've been thinking about building something but don't know the first step, "
            "comment START below. We'll guide you through it."
        ),
    },
    {
        "caption": "For the quiet ones.",
        "post": (
            "Some of you have been following this page for a while. "
            "Reading. Watching. Thinking.\n\n"
            "You haven't reached out yet — and that's okay. We understand completely.\n\n"
            "When you're ready, comment START below. No rush. No pressure. "
            "Just two people who are genuinely ready to listen."
        ),
    },
    {
        "caption": "A simple question.",
        "post": (
            "If someone told you five years ago that your life could look completely different today — "
            "more time, more choices, more breathing room — would you have believed them?\n\n"
            "We probably wouldn't have either. But here we are.\n\n"
            "Comment START if you're curious how we got here."
        ),
    },
    {
        "caption": "Real talk.",
        "post": (
            "We're not going to promise you overnight success or easy money. That's not what we do.\n\n"
            "What we can offer is a real conversation, a real path, and real support "
            "from two people who have walked this for over 14 years.\n\n"
            "If that sounds like what you need right now, comment START below."
        ),
    },
]


def get_cta_post(force_index: int = None) -> dict:
    """
    Returns a rotating CTA post — no Gemini call.
    Rotates by ISO week number ÷ 2 for bi-weekly cadence.
    force_index overrides rotation (for testing).
    """
    week = datetime.date.today().isocalendar()[1]
    idx = force_index if force_index is not None else (week // 2) % len(CTA_BANK)
    return CTA_BANK[idx]
