"""
image_generator.py
Generates Facebook post images for health news.
Format : 1080x1080 square (matches LP news-generator)
Layout :
  - Photo background (HF SDXL → HF SD1.5 → Pollinations flux → dark card fallback)
  - Dark gradient zone at bottom
  - LAWRENCE SIA / YOUR PERSONAL COACH logo bar above caption
  - Bold Montserrat headline at very bottom
  - Dark gray card (30,30,30) when all image generation fails
"""

import os
import time
import hashlib
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

# ── Dimensions ────────────────────────────────────────────────────────────────
IMAGE_WIDTH  = 1080
IMAGE_HEIGHT = 1080   # square, matches LP news-generator

# ── Credentials ───────────────────────────────────────────────────────────────
HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")

# ── HuggingFace endpoints ─────────────────────────────────────────────────────
HF_SDXL_LIGHTNING = "https://router.huggingface.co/hf-inference/models/ByteDance/SDXL-Lightning"
HF_SD15           = "https://router.huggingface.co/hf-inference/models/stable-diffusion-v1-5/stable-diffusion-v1-5"

SAFE_PROMPT = (
    "vibrant fresh healthy food flatlay, fruits vegetables superfoods, "
    "bright natural lighting, professional photography, square composition, no text, no words"
)

# ── Fonts — Montserrat from repo fonts/ folder, Liberation/DejaVu as fallback ─
_REPO_FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

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

# ── Image style pool — 32 health/wellness visual directions ───────────────────
STYLE_POOL = [
    # Food & nutrition
    "vibrant fresh fruit bowl flatlay, tropical colours, top-down view, bright natural light, square, no text",
    "colourful smoothie bowls and superfoods on white marble, clean minimal, square, no text",
    "fresh vegetables market scene, vivid greens and reds, rustic wooden background, square, no text",
    "close-up macro shot of fresh herbs and spices, bokeh background, warm golden tones, square, no text",
    "healthy meal prep containers, clean organised layout, bright kitchen, square, no text",
    "exotic tropical fruits sliced open, vibrant saturated colours, overhead shot, square, no text",
    "fresh salad greens with water droplets, macro photography, vivid colours, square, no text",
    "wholesome breakfast spread, warm morning light, cosy kitchen atmosphere, square, no text",
    # Nature & wellness
    "serene forest path at dawn, soft morning mist, green light through trees, square, no text",
    "ocean sunrise over calm water, warm golden hour light, horizon view, square, no text",
    "lush green rainforest waterfall, fresh and vibrant, nature photography, square, no text",
    "wildflower meadow in soft sunlight, bokeh background, warm pastel tones, square, no text",
    "mountain lake reflection at sunrise, crisp clean air, square, no text",
    "zen garden with smooth stones and bamboo, peaceful minimalist, soft natural light, square, no text",
    "dewy leaves in morning light, macro nature photography, ethereal beauty, square, no text",
    "cherry blossom branch against blue sky, soft pink tones, spring freshness, square, no text",
    # Active lifestyle
    "yoga on cliff overlooking ocean at sunrise, silhouette, square, no text",
    "morning run in city park, golden hour light, motion blur, energetic, square, no text",
    "cycling through autumn forest path, warm golden leaves, dynamic motion, square, no text",
    "swimming pool lane view, clear blue water, clean lines, healthy lifestyle, square, no text",
    "hiking boots on mountain trail, adventure lifestyle, rugged nature, square, no text",
    # Mindfulness & calm
    "hands holding warm cup of tea, cosy morning light, soft shallow depth of field, square, no text",
    "candle flame close-up, warm amber tones, soft bokeh, calm and peaceful, square, no text",
    "open book beside window with rain, cosy interior, warm light, peaceful mood, square, no text",
    "meditation stones balanced on calm water, zen minimalist, pastel tones, square, no text",
    "soft sunrise light through curtains, peaceful morning awakening, warm tones, square, no text",
    # Science & medical
    "abstract blue teal medical science background, clean lines, professional, square, no text",
    "DNA helix abstract visualization, blue glowing tones, modern science, square, no text",
    "clean laboratory glassware with colourful liquids, professional research, square, no text",
    # Lifestyle
    "happy healthy people outdoors, warm sunlight, candid lifestyle photography, square, no text",
    "farmer's market fresh produce, vibrant colours, community atmosphere, square, no text",
    "aerial view of green parks, fresh urban greenery, top-down perspective, square, no text",
]


def _load_font(paths: list, size: int) -> ImageFont.FreeTypeFont:
    for path in paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _build_prompt(headline: str) -> str:
    """Rotate through 32 styles by date + headline hash."""
    date_str  = datetime.now().strftime("%Y-%m-%d")
    hash_seed = int(hashlib.md5((date_str + headline[:30]).encode()).hexdigest(), 16)
    style     = STYLE_POOL[hash_seed % len(STYLE_POOL)]
    return f"{style}, high resolution, photorealistic, vibrant"


def _wrap_text(draw, text: str, font, max_width: int) -> list:
    words, lines, current = text.split(), [], ""
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


# ── Image generation ───────────────────────────────────────────────────────────

def _hf_call(prompt: str, api_url: str) -> Image.Image | None:
    """Call a HuggingFace model. Enforces divisible-by-8 dimensions."""
    if not HF_API_TOKEN:
        return None
    w = (min(IMAGE_WIDTH,  1024) // 8) * 8
    h = (min(IMAGE_HEIGHT, 1024) // 8) * 8
    try:
        resp = requests.post(
            api_url,
            headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
            json={
                "inputs": prompt,
                "parameters": {
                    "width":               w,
                    "height":              h,
                    "num_inference_steps": 4,   # SDXL-Lightning: 4 steps
                    "guidance_scale":      0,   # Lightning: guidance_scale=0
                }
            },
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
        print(f"  ⚠️  HF HTTP {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        print(f"  ⚠️  HF error: {e}")
    return None


def _pollinations(prompt: str) -> Image.Image | None:
    """Last-resort Pollinations fallback."""
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}"
    params = {
        "width":   IMAGE_WIDTH,
        "height":  IMAGE_HEIGHT,
        "nologo":  "true",
        "model":   "flux",
        "seed":    str(int(time.time()) % 99999),
    }
    for attempt in range(1, 3):
        try:
            print(f"  🎨 Pollinations attempt {attempt}/2...")
            resp = requests.get(url, params=params, timeout=90)
            if resp.status_code == 200:
                img = Image.open(BytesIO(resp.content)).convert("RGB")
                return img.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.LANCZOS)
            print(f"  ⚠️  Pollinations HTTP {resp.status_code}")
        except Exception as e:
            print(f"  ❌ Pollinations error: {e}")
        time.sleep(5)
    return None


def generate_background(prompt: str) -> Image.Image | None:
    """
    Priority:
    1. HuggingFace SDXL-Lightning (fast, high quality)
    2. HuggingFace SD 1.5 with safe prompt (reliable)
    3. Pollinations flux (last resort)
    4. None → dark card fallback in create_post_image
    """
    print("  🤗 Trying HuggingFace SDXL-Lightning...")
    img = _hf_call(prompt, HF_SDXL_LIGHTNING)
    if img:
        print(f"  ✅ SDXL-Lightning ({img.size[0]}x{img.size[1]}px)")
        return img

    print("  🤗 Trying HuggingFace SD 1.5...")
    img = _hf_call(SAFE_PROMPT, HF_SD15)
    if img:
        print(f"  ✅ SD 1.5 ({img.size[0]}x{img.size[1]}px)")
        return img

    print("  ⚠️  HuggingFace failed — trying Pollinations...")
    img = _pollinations(SAFE_PROMPT)
    if img:
        return img

    print("  ❌ All image providers failed.")
    return None


# ── Logo bar ───────────────────────────────────────────────────────────────────

def _draw_logo_bar(draw: ImageDraw.ImageDraw, w: int, y_top: int, bar_h: int = 56) -> None:
    """
    Draw the LAWRENCE SIA / YOUR PERSONAL COACH branding bar.
    Dark background, white name, grey subtitle, gold top line.
    """
    draw.rectangle([(0, y_top), (w, y_top + bar_h)], fill=(12, 12, 16, 220))

    font_brand    = _load_font(FONT_BOLD,   20)
    font_subtitle = _load_font(FONT_MEDIUM, 11)

    brand_text    = "LAWRENCE SIA"
    subtitle_text = "YOUR PERSONAL COACH"

    bb = draw.textbbox((0, 0), brand_text,    font=font_brand)
    sb = draw.textbbox((0, 0), subtitle_text, font=font_subtitle)
    bw = bb[2] - bb[0]
    sw = sb[2] - sb[0]

    draw.text(((w - bw) // 2, y_top + 7),  brand_text,    font=font_brand,    fill=(255, 255, 255))
    draw.text(((w - sw) // 2, y_top + 33), subtitle_text, font=font_subtitle, fill=(155, 155, 155))

    # Gold accent line at top of bar
    draw.rectangle([(0, y_top), (w, y_top + 2)], fill=(180, 120, 40))


# ── Text overlay ───────────────────────────────────────────────────────────────

def add_text_overlay(image: Image.Image, headline: str, tag: str = "HEALTH NEWS") -> Image.Image:
    """
    Photo post overlay layout (bottom to top):
    ┌─────────────────────────┐
    │   PHOTO (clean, top)    │
    │                         │
    │   ░░ dark gradient ░░   │
    │─────────────────────────│ ← gold line
    │   LAWRENCE SIA          │ ← logo bar
    │   YOUR PERSONAL COACH   │
    │─────────────────────────│
    │   Headline text         │ ← bold caption
    └─────────────────────────┘
    """
    w, h = image.size
    SIDE_PAD    = 50
    BOTTOM_PAD  = 36
    LOGO_BAR_H  = 56
    CAP_GAP     = 16

    # ── Tag badge (top-left) ──────────────────────────────────────────────────
    font_tag  = _load_font(FONT_BOLD, 22)
    tag_text  = f"  {tag}  "
    tag_bbox  = ImageDraw.Draw(image).textbbox((0, 0), tag_text, font=font_tag)
    tag_w     = tag_bbox[2] - tag_bbox[0] + 20
    tag_h     = tag_bbox[3] - tag_bbox[1] + 14

    # ── Measure caption first ─────────────────────────────────────────────────
    font = _load_font(FONT_EXTRABOLD, 54)
    temp_draw = ImageDraw.Draw(image)
    max_w = w - SIDE_PAD * 2

    def pixel_wrap(text, fnt, mx):
        words, lines, current = text.split(), [], ""
        for word in words:
            test = f"{current} {word}".strip()
            if temp_draw.textbbox((0, 0), test, font=fnt)[2] > mx and current:
                lines.append(current)
                current = word
            else:
                current = test
        if current:
            lines.append(current)
        return lines

    lines = pixel_wrap(headline, font, max_w)
    if len(lines) > 2:
        font  = _load_font(FONT_EXTRABOLD, 44)
        lines = pixel_wrap(headline, font, max_w)
    if len(lines) > 3:
        font  = _load_font(FONT_EXTRABOLD, 36)
        lines = pixel_wrap(headline, font, max_w)

    line_h       = int(font.size * 1.28)
    total_cap_h  = len(lines) * line_h

    # ── Calculate y positions bottom-up ──────────────────────────────────────
    cap_y_end   = h - BOTTOM_PAD
    cap_y_start = cap_y_end - total_cap_h
    logo_y_end  = cap_y_start - CAP_GAP
    logo_y_top  = logo_y_end - LOGO_BAR_H
    grad_h      = (h - logo_y_top) + 60

    # ── Dark gradient ─────────────────────────────────────────────────────────
    rgba    = image.convert("RGBA")
    overlay = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    for i in range(grad_h):
        alpha = int(240 * (i / grad_h))
        y = h - grad_h + i
        ov_draw.rectangle([(0, y), (w, y + 1)], fill=(0, 0, 0, alpha))
    image = Image.alpha_composite(rgba, overlay).convert("RGB")
    draw  = ImageDraw.Draw(image)

    # ── Tag badge ─────────────────────────────────────────────────────────────
    draw.rounded_rectangle([(SIDE_PAD, SIDE_PAD), (SIDE_PAD + tag_w, SIDE_PAD + tag_h)],
                           radius=6, fill=(220, 50, 50, 220))
    draw.text((SIDE_PAD + 10, SIDE_PAD + 7), tag_text, font=font_tag, fill=(255, 255, 255))

    # ── Logo bar ──────────────────────────────────────────────────────────────
    _draw_logo_bar(draw, w, logo_y_top, LOGO_BAR_H)

    # ── Headline caption ──────────────────────────────────────────────────────
    y = cap_y_start
    for line in lines:
        draw.text((SIDE_PAD + 2, y + 2), line, font=font, fill=(0, 0, 0, 150))
        draw.text((SIDE_PAD,     y),     line, font=font, fill=(255, 255, 255))
        y += line_h

    return image


def _create_dark_card(headline: str, tag: str = "HEALTH NEWS") -> Image.Image:
    """
    Dark gray card fallback when image generation fails completely.
    Background: (30, 30, 30) — dark charcoal, not pitch black.
    Logo bar at bottom, headline centred in usable space.
    """
    img  = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT), (30, 30, 30))
    draw = ImageDraw.Draw(img)
    w, h = img.size

    SIDE_PAD   = 60
    BOTTOM_PAD = 30
    LOGO_BAR_H = 56

    # Tag badge top-left
    font_tag = _load_font(FONT_BOLD, 22)
    tag_text = f"  {tag}  "
    tag_bbox = draw.textbbox((0, 0), tag_text, font=font_tag)
    tag_w    = tag_bbox[2] - tag_bbox[0] + 20
    tag_h    = tag_bbox[3] - tag_bbox[1] + 14
    draw.rounded_rectangle([(SIDE_PAD, SIDE_PAD), (SIDE_PAD + tag_w, SIDE_PAD + tag_h)],
                           radius=6, fill=(220, 50, 50, 220))
    draw.text((SIDE_PAD + 10, SIDE_PAD + 7), tag_text, font=font_tag, fill=(255, 255, 255))

    # Logo bar at very bottom
    logo_y_top = h - BOTTOM_PAD - LOGO_BAR_H
    _draw_logo_bar(draw, w, logo_y_top, LOGO_BAR_H)

    # Headline centred in usable space
    usable_top = SIDE_PAD + tag_h + 40
    usable_bot = logo_y_top - 20
    usable_h   = usable_bot - usable_top
    max_w      = w - SIDE_PAD * 2

    font  = _load_font(FONT_EXTRABOLD, 64)
    lines = _wrap_text(draw, headline, font, max_w)
    if len(lines) > 3:
        font  = _load_font(FONT_EXTRABOLD, 52)
        lines = _wrap_text(draw, headline, font, max_w)
    if len(lines) > 4:
        font  = _load_font(FONT_EXTRABOLD, 42)
        lines = _wrap_text(draw, headline, font, max_w)

    line_h      = int(font.size * 1.38)
    total_txt_h = len(lines) * line_h
    y           = usable_top + (usable_h - total_txt_h) // 2

    for line in lines:
        draw.text((SIDE_PAD, y), line, font=font, fill=(255, 255, 255))
        y += line_h

    return img


# ── Main entry point ───────────────────────────────────────────────────────────

def create_post_image(headline: str, output_path: str, category: str = "health",
                      source: str = "", tag: str = "HEALTH NEWS",
                      fallback_color: tuple = (30, 30, 30)) -> str | None:
    print(f'\n📸 Creating image: "{headline[:60]}..."')

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    prompt = _build_prompt(headline)
    bg     = generate_background(prompt)

    if bg is None:
        print("  ⚠️  Using dark card fallback.")
        final = _create_dark_card(headline, tag=tag)
    else:
        final = add_text_overlay(bg, headline, tag=tag)

    final.save(output_path, quality=92)
    print(f"  💾 Saved → {output_path}")
    return output_path


if __name__ == "__main__":
    os.makedirs("output_images", exist_ok=True)
    test_cases = [
        {"headline": "New Study: Poor Sleep Reduces Professional Performance by 40%",
         "output": "output_images/test_health.jpg"},
        {"headline": "5 Evidence-Based Habits That Protect Your Heart After 30",
         "output": "output_images/test_health2.jpg"},
    ]
    for tc in test_cases:
        create_post_image(headline=tc["headline"], output_path=tc["output"])
