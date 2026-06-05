"""
lp/brand_voice.py
Brand voice and content system for @lawrenceprecioussia.

STRATEGY: Attract strangers who don't know us yet.
Target: Filipino professionals in Singapore and Philippines who feel stuck,
underpaid, or quietly wondering if there's another way.
Goal: Make them feel seen → earn their follow → earn their trust → earn a conversation.

POST FORMATS (5 types, all prospect-attraction focused):
  TRUTH    — Bold statements they already believe but have never seen said out loud
  MATH     — Show the numbers of their life without mentioning any business
  REFRAME  — Challenge a belief that's keeping them stuck
  IDENTITY — Make the ideal prospect feel seen and called out in a good way
  QUESTION — Curiosity hooks that make them stop and think about their situation
"""

# ── System prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are writing Facebook posts for @lawrenceprecioussia — Lawrence and Precious Sia.

AUDIENCE: Filipino professionals in Singapore and the Philippines.
Nurses, engineers, IT workers, pharmacists, accountants.
Ages 25-45. Educated. Hardworking. Quietly wondering if there's another way.

VOICE:
- Bold but not arrogant
- Honest but not preachy
- Direct but not cold
- Like a friend who tells you the truth nobody else will say

RULES:
- NEVER mention USANA, MLM, network marketing, business opportunity, downline, upline,
  direct selling, commission, supplements, or any health products
- NEVER use "I" — write as "we" (Lawrence and Precious together) or address "you" directly
- NEVER sound like an ad
- NEVER give unsolicited advice — state observations, not prescriptions
- Short sentences. No filler words. No corporate language.
- The post should make someone stop scrolling, feel something, and want to share it"""

# ── New formats ────────────────────────────────────────────────────────────────
FORMATS = {
    "TRUTH":    "A bold statement the audience already believes but has never seen said out loud. No fluff. No setup. Just the truth.",
    "MATH":     "Show the real numbers of a Filipino professional's life. No narrative — just the math that makes people pause.",
    "REFRAME":  "Challenge one belief that's keeping them stuck. Start with what they were taught, pivot to what's actually true.",
    "IDENTITY": "Make the ideal prospect feel deeply seen. Describe who they are, what they carry, and what they quietly wonder.",
    "QUESTION": "One question that stops them mid-scroll and makes them think about their own situation. Easy to answer. Hard to ignore.",
}

# ── Weekly calendar — Mon/Wed/Thu/Sat/Sun only ─────────────────────────────────
# 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
WEEKLY_CALENDAR = {
    0: {"format": "TRUTH",    "type": "text"},   # Monday
    2: {"format": "MATH",     "type": "poll"},   # Wednesday — poll uses MATH format
    3: {"format": "REFRAME",  "type": "text"},   # Thursday
    5: {"format": "news",     "type": "news"},   # Saturday
    6: {"format": "faith",    "type": "faith"},  # Sunday
}

# Days with no automated post: Tuesday, Friday
ACTIVE_DAYS = {0, 2, 3, 5, 6}

# ── Image config ───────────────────────────────────────────────────────────────
IMAGE_TAG        = "LAWRENCE & PRECIOUS"
IMAGE_TAG_COLOR  = (180, 120, 40)
IMAGE_BG_FALLBACK = (12, 12, 16)
PAGE_HANDLE      = "@lawrenceprecioussia"

# ── Forbidden terms — 3-layer safety ─────────────────────────────────────────
FORBIDDEN_TERMS = [
    "usana", "mlm", "multi-level", "network marketing", "direct selling",
    "business opportunity", "income opportunity", "downline", "upline",
    "brand partner", "distributor", "gold director", "diamond director",
    "uem", "commission", "supplement", "health product",
    "join our team", "join us", "sign up", "register now",
]
