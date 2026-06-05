"""
lp/lp_post_generator.py
Post generators for @lawrenceprecioussia.

New strategy: attract strangers, not tell stories.
5 formats: TRUTH, MATH, REFRAME, IDENTITY, QUESTION
Each designed to make Filipino professionals feel seen and want to share.
"""

import re
import datetime
import random
from lp_gemini import call_gemini
from brand_voice import SYSTEM_PROMPT, FORMATS, FORBIDDEN_TERMS

# ─────────────────────────────────────────────────────────────────────────────
# CONTENT SEEDS — topic pools per format, rotated weekly
# ─────────────────────────────────────────────────────────────────────────────

TRUTH_TOPICS = [
    "having a stable job is not the same as having financial security",
    "most Filipino professionals are excellent at their job but underpaid for their potential",
    "working hard for someone else has a ceiling that working hard for yourself does not",
    "job security is something your employer controls, not you",
    "sending money home every month is love — but it also means you can never stop working",
    "most people plan their career but never plan their income",
    "being promoted at work and building wealth are two completely different things",
    "the safest-looking path is often the one with the least exit",
    "a good salary without a plan is just a comfortable trap",
    "loyalty to a company that can retrench you overnight is not a strategy",
    "most Filipinos were taught to find a good job, not to build something",
    "your income stops the moment you do — that's not freedom, that's dependency",
    "being busy and being productive with your future are not the same thing",
    "most people know they need another income source — almost nobody acts on it",
]

MATH_TOPICS = [
    "salary vs monthly expenses vs what's left for the future",
    "what happens to remittances over 10 years if nothing changes",
    "how much a typical Filipino professional in Singapore keeps after expenses",
    "the real cost of staying in a job you've outgrown",
    "how long your savings would last if your job stopped tomorrow",
    "what a 5% salary increase actually means after tax and expenses",
    "the gap between what you earn and what you actually keep",
    "how many years of work it takes to buy a house in Singapore vs Philippines",
    "what your monthly take-home becomes after rent, remittance, and daily expenses",
    "the math behind why two incomes change everything",
]

REFRAME_TOPICS = [
    "we were taught that a degree guarantees a good future — what it actually guarantees",
    "we were taught that saving money is enough — what saving without investing actually does",
    "we were taught that working harder gets you further — the ceiling most people hit",
    "we were taught to be grateful for a stable job — what stability actually costs",
    "we were taught that sacrifice now means comfort later — who decides when 'later' arrives",
    "we were told that your employer values your loyalty — what they value more",
    "we were raised to believe that one income is enough — when that stopped being true",
    "we were taught that asking for more is greedy — why staying silent costs more",
    "we believed that being employed meant being secure — the difference between a job and security",
    "we grew up thinking success means a good title — what success actually looks like at 40",
    "we were taught that the Philippines is the only place for family — what OFWs actually carry",
    "we were told that hard work always pays off — who it pays off for",
]

IDENTITY_TOPICS = [
    "the Filipino professional who works hard, sends money home, and still feels like it's never enough",
    "the one in the family who made it — and now carries everyone",
    "the professional who is excellent at their job but invisible in terms of building wealth",
    "the person who has a good life on paper but quietly wonders if this is all there is",
    "the Filipino in Singapore who left home to build a better future but isn't sure the future is building itself",
    "the professional who knows they need to do something different but doesn't know what or when",
    "the one who is always the reliable one — at work, at home, in the family — and is quietly exhausted",
    "the person who has been planning to start something for years but life keeps getting in the way",
    "the professional who earns well but somehow never gets ahead of expenses",
    "the Filipino parent who wants to give their children options they never had",
    "the one who watches others build something and thinks — why not me",
    "the professional who is great at executing someone else's vision but has never been asked about their own",
]

QUESTION_TOPICS = [
    "how long you could survive on savings if your income stopped tomorrow",
    "whether your current income will still be enough in 5 years given how prices keep rising",
    "what you would do differently if you had started building something on the side 3 years ago",
    "whether you are building towards something or just maintaining where you are",
    "what your financial life looks like when you are 55 if nothing changes",
    "how many income sources you currently have vs how many you would need to feel secure",
    "what you would do with your time if you didn't have to work for money",
    "whether the career path you are on is one you chose or one you fell into",
    "what one financial decision you made that you wish you had made differently",
    "what would have to change for you to feel genuinely financially free",
    "whether your parents' definition of success still fits your life",
    "what you are waiting for before you start building something of your own",
]

# ─────────────────────────────────────────────────────────────────────────────
# FALLBACK BANK — pre-written, no AI needed
# ─────────────────────────────────────────────────────────────────────────────

TRUTH_FALLBACKS = [
    {
        "image_hook": "A stable job is not financial security.",
        "post": "A stable job is not the same as financial security.\n\nThey look the same from the outside.\nBut one depends on your employer's decisions.\nThe other depends on yours.\n\nMost of us were never taught the difference.\n\nWhich one are you actually building right now?",
        "caption": "Worth sitting with.",
    },
    {
        "image_hook": "Your income stops the moment you do.",
        "post": "Your income stops the moment you do.\n\nThat's not freedom.\nThat's a well-paying dependency.\n\nMost people know this.\nAlmost nobody talks about it.\n\nWhat would it take for that to change for you?",
        "caption": "Real talk.",
    },
    {
        "image_hook": "You were taught to find a job. Not to build something.",
        "post": "Most of us were raised with one financial instruction:\nFind a good job. Keep it. Be grateful.\n\nNobody taught us to build something of our own.\nNobody taught us that a salary has a ceiling.\nNobody taught us what happens when the job ends.\n\nThat's not a blame game.\nIt's just information.\n\nWhat would you teach your children that nobody taught you?",
        "caption": "Think about this.",
    },
]

MATH_FALLBACKS = [
    {
        "image_hook": "SGD 4,000 salary. Let's do the math.",
        "post": "You earn SGD 4,000.\n\nRent: SGD 1,200.\nRemittance: SGD 1,000.\nFood and transport: SGD 600.\nPhone, insurance, subscriptions: SGD 200.\n\nWhat's left: SGD 1,000.\n\nTo save. To invest. To build. To handle emergencies.\n\nFor an entire month.\n\nDoes that number feel like enough to you?",
        "caption": "The honest math.",
    },
    {
        "image_hook": "How long would your savings last?",
        "post": "If your job stopped tomorrow —\nnot if you quit, but if it ended —\nhow long could you last on savings?\n\n1 month?\n3 months?\n6 months?\n\nMost people answer this question and go very quiet.\n\nThere's no wrong answer.\nBut there is an important one.\n\nWhat's yours?",
        "caption": "Be honest with yourself.",
    },
]

REFRAME_FALLBACKS = [
    {
        "image_hook": "Working harder has a ceiling. Most people find it too late.",
        "post": "We were taught that working harder gets you further.\n\nAnd it does — up to a point.\n\nBut working harder for someone else has a ceiling.\nYour employer decides where that ceiling is.\nYour performance review decides when you reach it.\nA business decision you had no part in can remove it entirely.\n\nWorking harder on something you own has a different equation.\n\nWhat's the ceiling on what you're building right now?",
        "caption": "Something to consider.",
    },
    {
        "image_hook": "Saving money is not enough anymore.",
        "post": "We were taught to save.\n\nSave for emergencies.\nSave for the future.\nSave, save, save.\n\nNobody told us that saving without growing means inflation quietly eats it.\nNobody told us that a savings account is not a plan.\nNobody told us that time is the one thing savings can't buy back.\n\nSaving is the floor.\nNot the ceiling.\n\nWhat are you doing above the floor?",
        "caption": "Ask yourself this.",
    },
]

IDENTITY_FALLBACKS = [
    {
        "image_hook": "This is for the one who carries everyone.",
        "post": "This is for the Filipino professional who:\n\nWorks hard every day.\nSends money home every month.\nShows up for the family.\nNever misses a deadline.\nSmiles through the exhaustion.\n\nAnd quietly, in between all of that,\nwonders if there's a version of this life\nwhere you're not always the one holding everything up.\n\nYou're not alone in that wondering.\n\nWhat does that version look like for you?",
        "caption": "You know who you are.",
    },
    {
        "image_hook": "Excellent at your job. Invisible in terms of wealth.",
        "post": "There's a type of person we see a lot.\n\nExcellent at their job.\nReliable. Hardworking. Respected.\n\nBut when it comes to building personal wealth?\nInvisible progress.\n\nNot because they're not smart enough.\nNot because they don't work hard enough.\n\nBut because everything they were taught\nwas about being good at someone else's goal.\n\nDoes any part of that feel familiar?",
        "caption": "We see you.",
    },
]

QUESTION_FALLBACKS = [
    {
        "image_hook": "What would you do if your job ended tomorrow?",
        "post": "Not if you quit.\nNot a career change.\n\nIf your job simply ended tomorrow —\nretrenchment, restructuring, whatever reason —\n\nWhat would you do?\n\nNot emotionally.\nPractically.\n\nHow long could you sustain your life?\nWhat options would you actually have?\n\nMost people avoid this question.\nThe ones who answer it honestly tend to make very different decisions.\n\nWhat's your honest answer?",
        "caption": "Worth thinking about.",
    },
    {
        "image_hook": "What are you waiting for?",
        "post": "There's something you've been thinking about starting.\n\nA side income.\nA skill to develop.\nSomething that's yours.\n\nAnd every few months you think about it,\ntell yourself soon,\nand then life gets in the way.\n\nWe're not judging.\nWe did the same thing for longer than we'd like to admit.\n\nBut we are asking:\n\nWhat exactly are you waiting for?",
        "caption": "Ask yourself this.",
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
    return m.group(1).strip().strip('"') if m else ""


def _safety_check(text: str) -> tuple:
    lower = text.lower()
    for term in FORBIDDEN_TERMS:
        if term in lower:
            return False, f"Forbidden term: '{term}'"
    return True, ""


def _get_topic(pool: list) -> str:
    week = datetime.date.today().isocalendar()[1]
    day  = datetime.date.today().toordinal()
    return pool[(week + day) % len(pool)]


def _get_fallback(pool: list) -> dict:
    week = datetime.date.today().isocalendar()[1]
    return pool[week % len(pool)]


# ─────────────────────────────────────────────────────────────────────────────
# FORMAT GENERATORS
# ─────────────────────────────────────────────────────────────────────────────

def _generate_post(fmt: str, topic: str, fallback_pool: list) -> dict:
    """Generic generator for TRUTH, REFRAME, IDENTITY, QUESTION formats."""

    format_instructions = {
        "TRUTH": (
            "Write a TRUTH BOMB post.\n"
            "One bold statement your audience already feels but has never seen said this clearly.\n"
            "No setup. No story. No fluff.\n"
            "Format: 1 bold opening statement, then 3-4 short lines that land the truth,\n"
            "then 1 question that makes them reflect on their own situation.\n"
            "Use line breaks between every thought. Maximum 60 words total."
        ),
        "REFRAME": (
            "Write a REFRAME post.\n"
            "Start with what they were taught or believe. Then pivot to what's actually true.\n"
            "Format: Start with 'We were taught...' or 'Most of us grew up believing...',\n"
            "then 3-4 short lines showing the gap between belief and reality,\n"
            "then 1 question that makes them examine their own situation.\n"
            "Use line breaks between every thought. Maximum 70 words total."
        ),
        "IDENTITY": (
            "Write an IDENTITY post.\n"
            "Make the ideal prospect feel deeply seen. Describe who they are with specificity.\n"
            "Format: Start with 'This is for...' or 'There's a type of person...',\n"
            "then 4-6 short lines describing their daily reality in detail,\n"
            "then 1-2 lines acknowledging what they quietly carry or wonder,\n"
            "then 1 gentle question that invites them to respond.\n"
            "Use line breaks. Maximum 80 words total."
        ),
        "QUESTION": (
            "Write a QUESTION post.\n"
            "One question that stops them mid-scroll and makes them think about their own life.\n"
            "Format: Set up the question with 2-3 short lines of context,\n"
            "then ask the question clearly,\n"
            "then 2-3 short lines that deepen it or make it harder to ignore.\n"
            "End with an invitation to answer. Maximum 60 words total."
        ),
    }

    instructions = format_instructions.get(fmt, format_instructions["TRUTH"])

    user_msg = (
        f"{instructions}\n\n"
        f"Topic angle: {topic}\n\n"
        f"AUDIENCE: Filipino professionals in Singapore and Philippines.\n"
        f"Nurses, engineers, IT workers. Ages 25-45. Hardworking. Quietly wondering if there's another way.\n\n"
        f"RULES:\n"
        f"- No stories, no 'we experienced this', no personal anecdotes\n"
        f"- Address 'you' directly OR make general statements about 'most people'\n"
        f"- Never mention any business, product, or opportunity\n"
        f"- English only\n"
        f"- Every line must earn its place — cut anything generic\n\n"
        f"Output format (exactly):\n"
        f"IMAGE_HOOK: [1 line, max 8 words — the single boldest thought from this post]\n"
        f"POST: [the full post with line breaks as described above]\n"
        f"CAPTION: [2-5 words — e.g. 'Worth sitting with.' / 'Real talk.' / 'Ask yourself this.' / 'We see you.']"
    )

    raw = call_gemini(user_msg, temperature=0.88, max_tokens=500)

    if raw:
        image_hook = _parse(raw, "IMAGE_HOOK", "POST")
        post       = _parse(raw, "POST", "CAPTION")
        caption    = _parse(raw, "CAPTION")

        safe, reason = _safety_check(post + " " + caption)
        if not safe:
            print(f"  ⚠️ Safety: {reason}. Using fallback.")
            return _get_fallback(fallback_pool)

        if post and image_hook:
            return {"image_hook": image_hook, "post": post, "caption": caption, "format": fmt}

    print(f"  ⚠️ Gemini failed for {fmt}. Using fallback.")
    return _get_fallback(fallback_pool)


def generate_truth_post() -> dict:
    topic = _get_topic(TRUTH_TOPICS)
    return _generate_post("TRUTH", topic, TRUTH_FALLBACKS)


def generate_reframe_post() -> dict:
    topic = _get_topic(REFRAME_TOPICS)
    result = _generate_post("REFRAME", topic, REFRAME_FALLBACKS)
    result["format"] = "REFRAME"
    return result


def generate_identity_post() -> dict:
    topic = _get_topic(IDENTITY_TOPICS)
    result = _generate_post("IDENTITY", topic, IDENTITY_FALLBACKS)
    result["format"] = "IDENTITY"
    return result


def generate_question_post() -> dict:
    topic = _get_topic(QUESTION_TOPICS)
    result = _generate_post("QUESTION", topic, QUESTION_FALLBACKS)
    result["format"] = "QUESTION"
    return result


def generate_text_post(post_format: str = "any") -> dict:
    """
    Route to the correct generator based on format or weekly calendar.
    post_format: TRUTH / REFRAME / IDENTITY / QUESTION / any
    """
    if post_format == "any":
        # Use weekly calendar
        day = datetime.date.today().weekday()
        calendar = {0: "TRUTH", 3: "REFRAME"}
        post_format = calendar.get(day, "IDENTITY")

    generators = {
        "TRUTH":    generate_truth_post,
        "REFRAME":  generate_reframe_post,
        "IDENTITY": generate_identity_post,
        "QUESTION": generate_question_post,
    }
    gen = generators.get(post_format.upper(), generate_identity_post)
    result = gen()
    print(f"\n  IMG HOOK: {result.get('image_hook', '')}")
    print(f"  FORMAT:   {result.get('format', post_format)}")
    print(f"  CAPTION:  {result.get('caption', '')}")
    print(f"  POST:\n  {result.get('post', '')[:200]}...")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# POLL GENERATOR — MATH format
# ─────────────────────────────────────────────────────────────────────────────

POLL_FALLBACK = {
    "question": "If your job ended tomorrow, how long could you last on savings?",
    "options": [
        "🅐  Less than 1 month — honestly",
        "🅑  1-3 months, then panic",
        "🅒  3-6 months, I'd be okay",
        "🅓  6+ months — I planned for this",
    ],
    "caption": "Be honest with yourself.",
    "fb_message": (
        "Be honest with yourself.\n\n"
        "If your job ended tomorrow, how long could you last on savings?\n\n"
        "🅐  Less than 1 month — honestly\n"
        "🅑  1-3 months, then panic\n"
        "🅒  3-6 months, I'd be okay\n"
        "🅓  6+ months — I planned for this\n\n"
        "Comment your answer below 👇"
    ),
}


def generate_poll_post() -> dict:
    """
    Wednesday poll — MATH format.
    Shows real financial numbers/scenarios, 4 relatable options.
    Designed to make people stop and honestly assess their situation.
    """
    week  = datetime.date.today().isocalendar()[1]
    topic = MATH_TOPICS[week % len(MATH_TOPICS)]

    user_msg = (
        f"Generate a Facebook poll for Filipino professionals in Singapore and Philippines.\n\n"
        f"TOPIC: {topic}\n\n"
        f"This is a MATH/REALITY CHECK poll. Make people stop and honestly assess their own situation.\n\n"
        f"Requirements:\n"
        f"- Question: specific, financial, relatable — no wrong answers but all answers sting a little\n"
        f"- 4 options that cover the realistic range from struggling to secure\n"
        f"- Each option: max 8 words, honest and a little painfully relatable\n"
        f"- English only — no Taglish\n"
        f"- NO mention of any business, product, or opportunity\n"
        f"- Do NOT reference any specific day of the week\n\n"
        f"Output EXACTLY:\n"
        f"QUESTION: [complete question]\n"
        f"A: [option]\n"
        f"B: [option]\n"
        f"C: [option]\n"
        f"D: [option]\n"
        f"CAPTION: [2-5 words — e.g. 'Be honest with yourself.' / 'The real number.' / 'Worth knowing.']"
    )

    raw = call_gemini(user_msg, temperature=0.88, max_tokens=400)

    if not raw:
        return POLL_FALLBACK

    print(f"\n--- Gemini raw (poll) ---\n{raw}\n---")

    question = opt_a = opt_b = opt_c = opt_d = caption = ""

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

    # Reject day-specific questions
    day_names = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday","weekend","weekday"]
    if any(d in question.lower() for d in day_names) or not question or not opt_a or not opt_b:
        print("  ⚠️ Poll rejected (day name or incomplete). Using fallback.")
        return POLL_FALLBACK

    options = [f"🅐  {opt_a}", f"🅑  {opt_b}", f"🅒  {opt_c}"]
    if opt_d:
        options.append(f"🅓  {opt_d}")

    fb_message = (
        f"{caption or 'Be honest with yourself.'}\n\n"
        f"{question}\n\n"
        + "\n".join(options)
        + "\n\nComment your answer below 👇"
    )

    return {"question": question, "options": options, "caption": caption, "fb_message": fb_message}


# ─────────────────────────────────────────────────────────────────────────────
# NEWS HOOK GENERATOR — unchanged, prospect-attraction framing
# ─────────────────────────────────────────────────────────────────────────────

def generate_news_hook(article: dict) -> dict:
    user_msg = (
        f"A news article relevant to our Filipino audience has been published.\n\n"
        f"Article title: {article.get('title', '')}\n"
        f"Source: {article.get('source', '')}\n"
        f"Summary: {article.get('summary', article.get('title', ''))[:300]}\n\n"
        f"Write a Facebook post for @lawrenceprecioussia.\n\n"
        f"TONE AND PURPOSE:\n"
        f"- Motivational, not fear-based. Inspire curiosity and possibility.\n"
        f"- The underlying message: building another income source matters.\n"
        f"- Do NOT say that directly. Let the reader arrive there themselves.\n"
        f"- Translate any jargon into plain everyday language.\n\n"
        f"FORMAT — write exactly in this style (short lines, no paragraphs):\n"
        f"Line 1: One hook sentence connecting the article to real life\n"
        f"Line 2: 'But let's be real:' bridge\n"
        f"Lines 3-5: 2-3 short punchy lines (4-8 words each)\n"
        f"Line 6: 'So the real question is...' pivot\n"
        f"Lines 7-9: 3 short options (e.g. Saving more? / Earning more? / Just keeping up?)\n"
        f"Line 10: Closing question inviting comments (max 12 words)\n"
        f"Line 11: 👇 Drop it in the comments\n\n"
        f"RULES:\n"
        f"- English only\n"
        f"- 'we/our' voice\n"
        f"- NO product/business/opportunity mentions\n"
        f"- Under 100 words\n\n"
        f"Output format:\n"
        f"POST: [the full post]\n"
        f"CAPTION: [2-5 words — e.g. 'Worth thinking about.' / 'Real talk.' / 'Something to consider.']"
    )

    raw = call_gemini(user_msg, temperature=0.88, max_tokens=400)

    if not raw:
        return {
            "post": f"Something in today's news got us thinking.\n\nBut let's be real:\nIt's not just a headline.\nIt's already affecting our wallets.\n\nSo the real question is...\n\nAre you adjusting?\nBuilding a buffer?\nOr just hoping it passes?\n\nWhat's your honest move right now?\n\n👇 Drop it in the comments",
            "caption": "Worth thinking about.",
            "article_url": article.get("url", ""),
        }

    post    = _parse(raw, "POST", "CAPTION")
    caption = _parse(raw, "CAPTION")

    safe, _ = _safety_check(post)
    if not safe:
        post = "Something in today's news got us thinking.\n\nBut let's be real:\nIt's not just a headline.\nIt's something most of us are quietly adjusting to.\n\nWhat are you paying more attention to these days?\n\n👇 Drop it in the comments"

    return {"post": post, "caption": caption, "article_url": article.get("url", "")}
