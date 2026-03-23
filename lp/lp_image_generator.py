"""
lp/lp_image_generator.py
Generates Facebook post images for @lawrenceprecioussia.

Format: 1080x1080 square (standard Facebook post)
Layout:
  - LAWRENCE & PRECIOUS logo bar at TOP
  - Photo background (HF → Pollinations → solid fallback)
  - Short bold caption at BOTTOM in dark gradient zone
  - Montserrat font (add fonts/ to repo) — falls back to Liberation Sans

Text card (Format A/B):
  - Dark background, logo at top, bold text centred in middle
"""

import os
import time
import hashlib
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from dotenv import load_dotenv
from brand_voice import IMAGE_TAG, IMAGE_TAG_COLOR, IMAGE_BG_FALLBACK, PAGE_HANDLE

load_dotenv()

IMAGE_WIDTH  = 1080
IMAGE_HEIGHT = 1080

HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# HuggingFace model endpoints
HF_SDXL_LIGHTNING = "https://router.huggingface.co/hf-inference/models/ByteDance/SDXL-Lightning"
HF_SD15           = "https://router.huggingface.co/hf-inference/models/stable-diffusion-v1-5/stable-diffusion-v1-5"

SAFE_PROMPT = (
    "happy couple walking together in city park, warm golden hour sunlight, "
    "candid lifestyle photography, square composition, no text, no words"
)

_REPO_FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts")

FONT_EXTRABOLD = [
    os.path.join(_REPO_FONTS, "Montserrat-ExtraBold.ttf"),
    os.path.join(_REPO_FONTS, "Montserrat-Bold.ttf"),
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
FONT_BOLD = [
    os.path.join(_REPO_FONTS, "Montserrat-Bold.ttf"),
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
FONT_MEDIUM = [
    os.path.join(_REPO_FONTS, "Montserrat-Medium.ttf"),
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
FONT_REGULAR = FONT_MEDIUM

STYLE_POOL = [
    "happy couple laughing outdoors, golden hour sunlight, warm bokeh, square composition, no text",
    "husband and wife having coffee on balcony, city skyline, morning light, square, no text",
    "couple walking hand in hand on beach at sunset, warm silhouette, square, no text",
    "family picnic in green park, golden afternoon, candid joy, square, no text",
    "couple cooking together in bright kitchen, warm domestic scene, square, no text",
    "husband and wife on hillside overlooking city at dusk, square, no text",
    "couple laughing over meal at outdoor cafe, warm evening light, square, no text",
    "parents and child playing at park, golden hour, square, no text",
    "couple high-fiving after achievement, warm celebratory, square, no text",
    "morning coffee by large window, city skyline, calm, square, no text",
    "laptop on cafe table, person looking out window, morning light, square, no text",
    "cosy home office with plants, natural light, warm tones, square, no text",
    "sunrise from Singapore apartment balcony, aspirational, square, no text",
    "travel couple at airport, adventure, warm tones, square, no text",
    "couple running on coastal road, morning light, energetic, square, no text",
    "family at weekend market, vibrant produce, warm, square, no text",
    "quiet morning, couple reading together, warm blankets, square, no text",
    "tropical garden in golden sunlight, serene, square, no text",
    "sunset silhouette over sea, couple together, golden, square, no text",
    "Singapore skyline at dusk, warm city glow, square, no text",
    "professional at bright desk by window, calm, square, no text",
    "two professionals collaborating, warm office, square, no text",
    "couple celebrating over dinner, warm restaurant, square, no text",
    "person journaling in sunlit cafe, warm amber, square, no text",
]


def _load_font(paths: list, size: int) -> ImageFont.FreeTypeFont:
    for path in paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _build_prompt(post_text: str, tone: str = "warm") -> str:
    """
    Build image prompt based on emotional tone of the post.
    tone options: "warm" (lifestyle), "serious" (financial/news), "faith" (calm/spiritual)
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    seed = int(hashlib.md5((date_str + post_text[:30]).encode()).hexdigest(), 16)

    if tone == "serious":
        # Financial stress / news — urban, tighter, more grounded
        pool = [
            "Filipino family checking grocery receipts at supermarket, worried expression, fluorescent lighting, realistic, no text",
            "person looking at phone with financial news, urban Singapore street, overcast day, candid, no text",
            "empty wallet on table next to grocery bags, hard light, stark, realistic, no text",
            "busy wet market in Philippines, crowded, prices on signs, documentary style, no text",
            "couple reviewing bills at home kitchen table, evening light, concerned, no text",
            "long queue at ATM machine, urban setting, overcast, documentary photography, no text",
            "hands counting peso bills on table, tight budget feel, realistic, no text",
            "fuel pump at gas station, price display visible but blurred, urban Philippines, no text",
            "empty plate next to calculator and receipts, hard honest lighting, no text",
            "commuter on MRT looking tired, urban Singapore, candid street photography, no text",
            "Filipino worker checking phone in break room, stressed expression, fluorescent light, no text",
            "supermarket shelf with price tags, shopper looking concerned, realistic, no text",
        ]
    elif tone == "faith":
        # Sunday faith posts — peaceful, light, spiritual
        pool = [
            "open Bible on wooden table, morning light, warm golden, peaceful, no text",
            "hands clasped in prayer, soft window light, serene, no text",
            "sunrise over calm ocean, golden horizon, peaceful and hopeful, no text",
            "church interior with light streaming through windows, warm and peaceful, no text",
            "lone tree on hill at sunrise, spiritual, calm, golden tones, no text",
            "couple sitting quietly together watching sunset, peaceful, no text",
            "candle flame in dark room, warm amber glow, contemplative, no text",
            "open hands receiving light, spiritual symbolism, warm tones, no text",
        ]
    else:
        # Default warm lifestyle pool
        pool = STYLE_POOL

    style = pool[seed % len(pool)]
    base = "high resolution, photorealistic, square composition, no text, no words"
    return f"{style}, {base}"


def _wrap_text(draw, text: str, font, max_width: int) -> list:
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        if draw.textbbox((0, 0), test, font=font)[2] > max_width and current:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def _shorten_for_image(text: str, max_chars: int = 70, tone: str = "warm") -> str:
    """
    Pick the catchiest 1-line hook for the image overlay.
    tone="serious" prioritises urgency and impact words.
    tone="warm"    prioritises relatable couple/human moments.
    """
    import re as _re
    sentences = _re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 15]

    if not sentences:
        return text[:max_chars]

    def score(s):
        pts = 0
        sl  = s.lower()
        if 20 <= len(s) <= max_chars:    pts += 6
        if s.endswith("?"):              pts += 4
        if s.endswith("!"):              pts += 2
        if len(s) < 40:                  pts -= 2
        if len(s) > max_chars:           pts -= 10

        if tone == "serious":
            # Financial/news — urgency and impact words score higher
            for w in ["prices", "money", "wallet", "bills", "budget", "costs",
                      "expensive", "afford", "tight", "loans", "peso",
                      "already", "still", "harder", "feel it", "noticed"]:
                if w in sl: pts += 3
        else:
            # Warm/couple — relatable "we" moments score higher
            for w in ["we", "us", "our", "remember", "imagine", "still",
                      "somehow", "both", "never", "always"]:
                if w in sl: pts += 2

        return pts

    best = max(sentences, key=score)
    if len(best) > max_chars:
        best = best[:max_chars].rsplit(" ", 1)[0] + "..."
    return best


def _draw_logo_bar(draw: ImageDraw.ImageDraw, w: int, y_top: int, bar_h: int = 56) -> None:
    """
    Draw the LAWRENCE & PRECIOUS logo bar at a specified y position.
    Used above the caption text, inside the dark gradient zone.
    """
    draw.rectangle([(0, y_top), (w, y_top + bar_h)], fill=(12, 12, 16, 220))

    font_brand    = _load_font(FONT_BOLD,   20)
    font_subtitle = _load_font(FONT_MEDIUM, 11)

    brand_text    = "LAWRENCE & PRECIOUS"
    subtitle_text = "YOUR BUSINESS MENTORS"

    bb = draw.textbbox((0, 0), brand_text, font=font_brand)
    bw = bb[2] - bb[0]
    sb = draw.textbbox((0, 0), subtitle_text, font=font_subtitle)
    sw = sb[2] - sb[0]

    draw.text(((w - bw) // 2, y_top + 7),  brand_text,    font=font_brand,    fill=(255, 255, 255))
    draw.text(((w - sw) // 2, y_top + 33), subtitle_text, font=font_subtitle, fill=(155, 155, 155))

    # Thin gold line at top of bar
    draw.rectangle([(0, y_top), (w, y_top + 2)], fill=(180, 120, 40))


def _gemini_image(prompt: str) -> Image.Image | None:
    """
    Primary image generator — Gemini 3.1 Flash Image Preview.
    Free tier: ~500 requests/day. Returns inline base64 PNG.
    """
    if not GEMINI_API_KEY:
        return None
    try:
        from google import genai as gai
        from google.genai import types as gtypes
        client = gai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents=prompt,
            config=gtypes.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=gtypes.ImageConfig(
                    aspect_ratio="1:1",
                    image_size="1K",
                )
            ),
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                img = Image.open(BytesIO(part.inline_data.data)).convert("RGB")
                return img.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.LANCZOS)
        print("  ⚠️ Gemini image: no image part in response")
        return None
    except Exception as e:
        print(f"  ⚠️ Gemini image error: {e}")
        return None


def _hf_call(prompt: str, api_url: str) -> Image.Image | None:
    """HuggingFace Inference API — used as fallback."""
    if not HF_API_TOKEN:
        return None
    w = (min(IMAGE_WIDTH, 1024) // 8) * 8
    h = (min(IMAGE_HEIGHT, 1024) // 8) * 8
    try:
        resp = requests.post(
            api_url,
            headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
            json={"inputs": prompt, "parameters": {
                "width": w, "height": h,
                "num_inference_steps": 4,   # SDXL-Lightning uses 4 steps
                "guidance_scale": 0,        # Lightning requires guidance_scale=0
            }},
            timeout=120,
        )
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content)).convert("RGB")
            return img.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.LANCZOS)
        if resp.status_code == 503:
            print("  ⏳ HF model loading, waiting 20s...")
            time.sleep(20)
            resp2 = requests.post(
                api_url,
                headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
                json={"inputs": prompt},
                timeout=120,
            )
            if resp2.status_code == 200:
                img = Image.open(BytesIO(resp2.content)).convert("RGB")
                return img.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.LANCZOS)
        print(f"  ⚠️ HF HTTP {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        print(f"  ⚠️ HF error: {e}")
    return None


def generate_background(prompt: str) -> Image.Image | None:
    """
    Image generation pipeline:
    1. Gemini 3.1 Flash Image Preview (primary — free tier ~500/day)
    2. HuggingFace SDXL-Lightning (fallback 1 — fast 4-step distilled)
    3. HuggingFace SD 1.5 (fallback 2 — reliable, lightweight)
    4. None → text card fallback handled by caller
    """
    print("  🎨 Trying Gemini image generation...")
    img = _gemini_image(prompt)
    if img:
        print(f"  ✅ Gemini image ({img.size[0]}x{img.size[1]}px)")
        return img

    print("  🤗 Trying HuggingFace SDXL-Lightning...")
    img = _hf_call(prompt, HF_SDXL_LIGHTNING)
    if img:
        print(f"  ✅ SDXL-Lightning image ({img.size[0]}x{img.size[1]}px)")
        return img

    print("  🤗 Trying HuggingFace SD 1.5...")
    img = _hf_call(SAFE_PROMPT, HF_SD15)
    if img:
        print(f"  ✅ SD 1.5 image ({img.size[0]}x{img.size[1]}px)")
        return img

    print("  ❌ All image providers failed — will use text card.")
    return None


def add_text_overlay(image: Image.Image, post_text: str, tone: str = "warm") -> Image.Image:
    """
    Photo post overlay — layout (bottom to top):
      ┌─────────────────────────┐
      │   PHOTO (clean, top)    │
      │                         │
      │   ░░ dark gradient ░░   │
      │─────────────────────────│  ← gold line
      │  LAWRENCE & PRECIOUS    │  ← logo bar
      │  YOUR BUSINESS MENTORS  │
      │─────────────────────────│
      │  Caption hook text      │  ← 1-2 lines bold
      └─────────────────────────┘
    """
    w, h = image.size
    SIDE_PAD    = 50
    BOTTOM_PAD  = 36   # gap from very bottom edge
    LOGO_BAR_H  = 56   # height of logo bar
    CAP_GAP     = 16   # gap between logo bar and caption text

    # ── Short caption text — measure first ───────────────────────────────────
    short_text = _shorten_for_image(post_text, max_chars=70, tone=tone)
    font       = _load_font(FONT_EXTRABOLD, 54)
    max_w      = w - SIDE_PAD * 2

    # Need draw object to measure text — create on original image first
    temp_draw = ImageDraw.Draw(image)
    lines = _wrap_text(temp_draw, short_text, font, max_w)
    if len(lines) > 2:
        font  = _load_font(FONT_EXTRABOLD, 44)
        lines = _wrap_text(temp_draw, short_text, font, max_w)
    if len(lines) > 3:
        font  = _load_font(FONT_EXTRABOLD, 36)
        lines = _wrap_text(temp_draw, short_text, font, max_w)

    line_h      = int(font.size * 1.28)
    total_cap_h = len(lines) * line_h

    # ── Calculate y positions bottom-up ──────────────────────────────────────
    cap_y_end   = h - BOTTOM_PAD               # bottom of caption
    cap_y_start = cap_y_end - total_cap_h      # top of caption
    logo_y_end  = cap_y_start - CAP_GAP        # bottom of logo bar
    logo_y_top  = logo_y_end - LOGO_BAR_H      # top of logo bar

    # Total dark zone height needed
    dark_zone_h = h - logo_y_top + 20

    # ── Dark gradient covering bottom portion ─────────────────────────────────
    rgba    = image.convert("RGBA")
    overlay = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    grad_h  = dark_zone_h + 60   # extend gradient a bit higher for smooth fade
    for i in range(grad_h):
        alpha = int(240 * (i / grad_h))
        y = h - grad_h + i
        ov_draw.rectangle([(0, y), (w, y + 1)], fill=(0, 0, 0, alpha))
    image = Image.alpha_composite(rgba, overlay).convert("RGB")

    draw = ImageDraw.Draw(image)

    # ── Logo bar above caption ────────────────────────────────────────────────
    _draw_logo_bar(draw, w, logo_y_top, LOGO_BAR_H)

    # ── Caption text at very bottom ───────────────────────────────────────────
    y = cap_y_start
    for line in lines:
        draw.text((SIDE_PAD + 2, y + 2), line, font=font, fill=(0, 0, 0, 150))
        draw.text((SIDE_PAD,     y),     line, font=font, fill=(255, 255, 255))
        y += line_h

    return image


def create_post_image(post_text: str, output_path: str, use_text_card: bool = False, tone: str = "warm") -> str | None:
    if use_text_card:
        # Format A/B explicitly requested text card — show full post text
        return create_text_card(post_text, output_path, tone="warm")

    print(f'\nCreating LP image: "{post_text[:55]}..."')
    prompt = _build_prompt(post_text, tone=tone)
    bg = generate_background(prompt)

    if bg is None:
        print("  Image generation failed — falling back to text card.")
        # Fallback for news/wisdom — show hook only, not full post
        return create_text_card(post_text, output_path, tone=tone)

    final = add_text_overlay(bg, post_text, tone=tone)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    final.save(output_path, quality=92)
    print(f"  Saved → {output_path}")
    return output_path


def create_text_card(post_text: str, output_path: str, tone: str = "warm") -> str | None:
    """
    Dark card layout.
    For Format A/B (tone=warm): shows full post text centred — the post IS the card.
    For news/wisdom fallback (tone=serious/faith): shows only the short hook,
    matching what add_text_overlay would show if HuggingFace had succeeded.
    """
    print(f'\nCreating text card: "{post_text[:55]}..."')

    # Decide what text to show on the card
    if tone == "warm":
        display_text = post_text          # Format A/B — full text is the point
    else:
        display_text = _shorten_for_image(post_text, max_chars=70, tone=tone)

    img  = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT), (12, 12, 16))
    draw = ImageDraw.Draw(img)
    w, h = img.size

    LOGO_BAR_H  = 56
    BOTTOM_PAD  = 30
    SIDE_PAD    = 60

    # ── Logo bar at bottom ────────────────────────────────────────────────────
    logo_y_top = h - BOTTOM_PAD - LOGO_BAR_H
    _draw_logo_bar(draw, w, logo_y_top, LOGO_BAR_H)

    # ── Text centred in space above logo bar ──────────────────────────────────
    usable_top = 40
    usable_bot = logo_y_top - 20
    usable_h   = usable_bot - usable_top

    # Start font size — larger for short hooks, standard for full post text
    start_size = 72 if tone != "warm" else 64
    font  = _load_font(FONT_EXTRABOLD, start_size)
    max_w = w - SIDE_PAD * 2
    lines = _wrap_text(draw, display_text, font, max_w)

    if len(lines) > 3:
        font  = _load_font(FONT_EXTRABOLD, 54)
        lines = _wrap_text(draw, display_text, font, max_w)
    if len(lines) > 4:
        font  = _load_font(FONT_EXTRABOLD, 44)
        lines = _wrap_text(draw, display_text, font, max_w)

    line_h      = int(font.size * 1.38)
    total_txt_h = len(lines) * line_h
    y           = usable_top + (usable_h - total_txt_h) // 2

    for line in lines:
        draw.text((SIDE_PAD, y), line, font=font, fill=(255, 255, 255))
        y += line_h

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    img.save(output_path, quality=95)
    print(f"  Text card saved → {output_path}")
    return output_path
