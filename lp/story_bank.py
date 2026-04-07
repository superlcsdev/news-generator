"""
lp/story_bank.py
Real couple story seeds for @lawrenceprecioussia.

ALL stories here are real events from Lawrence and Precious's journey.
Gemini must stay strictly within what each story describes.
No invented details, no embellishment beyond what the seed contains.
"""

import random
import datetime

# ─────────────────────────────────────────────────────────────────────────────
# STORY BANK — real verified stories only
# Each entry: seed (what happened), angle (how to frame it), lesson (the takeaway)
# ─────────────────────────────────────────────────────────────────────────────

STORY_BANK = {

    # ── FIRST STEPS ───────────────────────────────────────────────────────────
    "first_steps": [
        {
            "seed": (
                "Our very first business presentation was in Singapore, to Precious's housemate — "
                "a motherly figure who patiently sat through the whole thing. "
                "Precious covered the products side, Lawrence covered the business side. "
                "Neither of us really knew how to present effectively. We just did it anyway. "
                "She politely declined the business, but bought some products after some time. "
                "Looking back, if we hadn't taken that first step that day, none of what followed would have happened."
            ),
            "angle": "We didn't start because we were ready. We started because we decided to.",
            "lesson": "The first step doesn't have to be good. It just has to happen.",
            "theme": "entrepreneurship",
        },
    ],

    # ── EARLY STRUGGLE ────────────────────────────────────────────────────────
    "struggle": [
        {
            "seed": (
                "Early in the business, we organised an awarding event. "
                "When it was time to host, nobody was able to step up and do it. "
                "It was an embarrassing situation. "
                "Lawrence went up on stage and hosted anyway — not because he was confident, "
                "but because someone had to. It didn't go perfectly. "
                "But the lesson stayed: leaders step up even when the task isn't comfortable."
            ),
            "angle": "Nobody was ready to host. So Lawrence just went up anyway.",
            "lesson": "Leadership isn't about being the most qualified. It's about being willing when others aren't.",
            "theme": "entrepreneurship",
        },
        {
            "seed": (
                "During a small team presentation, Precious and other leaders were sharing to a guest "
                "who was not in the mood to listen. He kept interrupting and challenging everything. "
                "The situation escalated to the point where the guest wanted to fight. "
                "The team managed to de-escalate before it got worse. "
                "Not every presentation ends the way you hope — and that's part of the journey."
            ),
            "angle": "Some guests challenge everything. Some situations don't end well. You show up anyway.",
            "lesson": "You can't control the room. You can only control how you handle it.",
            "theme": "entrepreneurship",
        },
        {
            "seed": (
                "During a presentation with just a few guests, Precious was really energetic and hyped up. "
                "At one point she said Albert Einstein was the first person to receive the Albert Einstein Award. "
                "Lawrence was sitting right beside her and was completely caught off guard. "
                "But Precious was so energetic that the guests didn't even notice the mistake. "
                "They carried on. The guests signed up. "
                "Lesson learned: sometimes how you say it matters more than what you say."
            ),
            "angle": "She said Albert Einstein won the Albert Einstein Award. The guests still signed up.",
            "lesson": "Energy and conviction can carry a room even when the words aren't perfect.",
            "theme": "entrepreneurship",
        },
        {
            "seed": (
                "We lost $600 worth of customer products on a restaurant table at 1am "
                "during a push for a major rank. "
                "We almost quit that night. "
                "We stayed because of the team we had already promised to help."
            ),
            "angle": "We almost quit at 1am over $600. We stayed because of the people.",
            "lesson": "The reason you stay is rarely about the money. It's almost always about the people.",
            "theme": "entrepreneurship",
        },
    ],

    # ── LEAVING THE JOB ───────────────────────────────────────────────────────
    "turning_points": [
        {
            "seed": (
                "For the year before Lawrence resigned, he was managing a demanding IT project management role "
                "that frequently sent him to Mauritius to gather user requirements and align the development team. "
                "On top of that, he was building the business part-time. "
                "The hardest part was the constant mental switching — from IT project manager mode "
                "to business mentor mode, sometimes multiple times a day. "
                "He slept less. He worked more hours. But he knew the business was the path to freedom. "
                "When the business income hit the target, he resigned. "
                "Walking out on the last day felt like relief — like a weight finally lifted. "
                "His colleagues were supportive."
            ),
            "angle": "Mauritius trips, late nights, two modes, one goal.",
            "lesson": "The season of wearing two hats is hard. But it has a finish line — if you don't stop.",
            "theme": "finance",
        },
        {
            "seed": (
                "Precious resigned first — paid back her bond, walked away from her career and her NUS university place "
                "on the same day. One decision closed two doors at once. "
                "Lawrence watched her do it and knew his turn was coming. "
                "They had made a deal early on: whoever hits the income goal first, the other follows. "
                "She went first."
            ),
            "angle": "She paid the bond. She gave up NUS. She went first. Of course she did.",
            "lesson": "Watching your partner bet on themselves is one of the most motivating things you will ever see.",
            "theme": "entrepreneurship",
        },
    ],

    # ── COUPLE DYNAMIC ────────────────────────────────────────────────────────
    "couple_dynamic": [
        {
            "seed": (
                "Lawrence and Precious have opposite default modes. "
                "Lawrence wants the system ready before he starts. "
                "Precious just starts. "
                "Their ongoing tension: Lawrence says let me prepare properly first, "
                "Precious says set the appointment and we'll figure it out. "
                "They usually find a middle ground — but Precious's instinct to start has been right more often than not. "
                "The lesson they keep learning: you don't start when you're great. You start to be great."
            ),
            "angle": "He wants to be ready. She sets the appointment anyway.",
            "lesson": "You don't start when you're great. You start to be great.",
            "theme": "entrepreneurship",
        },
        {
            "seed": (
                "Early in the business, Lawrence would attend a training and then spend a long time "
                "preparing before he felt ready to train others. "
                "Precious would already be setting appointments — sometimes so soon that Lawrence "
                "felt he wasn't ready yet. "
                "But once the appointment was locked in, the deadline pushed him. "
                "He prepared faster. He delivered. It worked. "
                "The external deadline did what weeks of preparation couldn't."
            ),
            "angle": "She set the appointment before he felt ready. The deadline did the rest.",
            "lesson": "Sometimes the best preparation is a deadline you can't escape.",
            "theme": "entrepreneurship",
        },
        {
            "seed": (
                "Lawrence handles the numbers and strategy side of the business. "
                "Precious handles the people and energy side. "
                "They didn't sit down and plan it this way — it emerged naturally over time. "
                "She lights up a room. He keeps the systems running. "
                "Together they cover what neither could do alone."
            ),
            "angle": "She brings the energy. He builds the system. Neither could do the other's job.",
            "lesson": "The best partnerships aren't two of the same person. They're two different people who fit.",
            "theme": "couple",
        },
    ],

    # ── GROWTH ────────────────────────────────────────────────────────────────
    "growth": [
        {
            "seed": (
                "When they ran for a major rank advancement, the whole team rallied together. "
                "The final push lasted a few weeks — intense, focused, everyone contributing. "
                "When they hit the goal, it proved something beyond the rank itself: "
                "that Filipinos in Singapore could build a business and take it to the next level. "
                "After they reached the goal, teammates who had been watching got motivated to run for their own goals. "
                "The duplication that followed was exponential."
            ),
            "angle": "The rank proved it was possible. The team ran with that proof.",
            "lesson": "When you achieve something, you don't just earn a title. You give your team permission to believe.",
            "theme": "entrepreneurship",
        },
    ],

    # ── ORIGIN ────────────────────────────────────────────────────────────────
    "origin": [
        {
            "seed": (
                "Lawrence was introduced to the business by his thesis mate from De La Salle University. "
                "He was skeptical. But his first thought wasn't about himself — it was about Precious. "
                "He thought it might work for them, as a couple. "
                "They weren't even married yet. They had been together just over a year."
            ),
            "angle": "He was skeptical. But his first thought was of her.",
            "lesson": "Some of the best decisions we make aren't really about us.",
            "theme": "entrepreneurship",
        },
        {
            "seed": (
                "Between them: one in medicine, one in IT. "
                "Exactly what Filipino parents dream for their children. "
                "Good jobs, stable income, respectable careers. "
                "And they still chose to build something else on the side — not because life was bad, "
                "but because they wanted something more."
            ),
            "angle": "Good jobs. Stable life. Still wanted more.",
            "lesson": "Contentment and ambition can coexist. One doesn't cancel the other.",
            "theme": "finance",
        },
    ],

    # ── MARRIAGE ──────────────────────────────────────────────────────────────
    "marriage": [
        {
            "seed": (
                "They built the business before they really knew each other deeply. "
                "The process of building it together — the disagreements, the compromises, "
                "the late nights, the different approaches — was how they learned who they each were. "
                "Not separately. Together."
            ),
            "angle": "Building the business taught them more about each other than anything else.",
            "lesson": "Shared struggle reveals character faster than comfortable times ever will.",
            "theme": "couple",
        },
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# FORMAT → THEME MAPPING
# ─────────────────────────────────────────────────────────────────────────────

FORMAT_THEME_MAP = {
    "A":  ["struggle", "turning_points"],
    "B":  ["couple_dynamic", "struggle"],
    "BW": ["couple_dynamic", "marriage"],
    "C":  ["marriage", "growth", "turning_points"],
    "D":  ["turning_points", "origin", "marriage"],
    "E":  ["growth"],
}


def get_seed_for_format(post_format: str) -> dict:
    themes = FORMAT_THEME_MAP.get(post_format, ["origin"])
    day_idx = datetime.date.today().toordinal() + ord(post_format[0])
    theme = themes[day_idx % len(themes)]
    seeds = STORY_BANK.get(theme, [])
    if not seeds:
        seeds = STORY_BANK.get("first_steps", [{}])
    seed = seeds[day_idx % len(seeds)]
    return seed


def get_seed_context(post_format: str) -> str:
    seed = get_seed_for_format(post_format)
    if not seed:
        return ""
    return (
        f"REAL STORY — this is what actually happened. Base the post on these facts only:\n"
        f"---\n"
        f"{seed['seed']}\n"
        f"---\n"
        f"Suggested angle: {seed['angle']}\n"
        f"Core lesson: {seed['lesson']}\n\n"
        f"STRICT RULES:\n"
        f"- Only narrate events explicitly described above — no invented details\n"
        f"- Do NOT add dialogue, scenes, or emotions not mentioned in the story\n"
        f"- Do NOT change what happened — only how it is expressed\n"
        f"- The lesson must come directly from the real events above\n"
        f"- Write in 'we/our' voice — Lawrence and Precious telling it together\n"
        f"- If the story is funny, let it be funny — don't dramatise it\n"
        f"- If the story is quiet, let it be quiet — don't inflate it"
    )
