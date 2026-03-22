"""
lp/lp_image_generator.py
Generates Facebook post images for @lawrenceprecioussia.

Adapted from ../image_generator.py — same HuggingFace → Pollinations pipeline,
same font loading, same Pillow overlay pattern.

Key differences:
  - Warm couple/lifestyle visual style pool (not health/food)
  - Gold tag badge "LAWRENCE & PRECIOUS" (not red "HEALTH NEWS")
  - @lawrenceprecioussia handle watermark bottom-right
  - Warm dark fallback background colour
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

IMAGE_WIDTH  = 1200
IMAGE_HEIGHT = 632

HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
HF_SDXL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
HF_SD21  = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-2-1"

SAFE_PROMPT = (
    "happy couple walking together in city park, warm golden hour sunlight, "
    "candid lifestyle photography, no text, no words"
)

# Font paths — identical fallback chain to your image_generator.py
FONT_BOLD = [
    "arialbd.ttf", "Arial_Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
FONT_REGULAR = [
    "arial.ttf", "Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]

# ── Visual style pool — warm, couple-focused, Filipino-relatable ──────────────
STYLE_POOL = [
    # Couple & family
    "happy couple laughing outdoors, golden hour sunlight, warm bokeh, candid, no text",
    "husband and wife having coffee on balcony, city skyline view, morning light, peaceful, no text",
    "couple walking hand in hand on beach at sunset, warm silhouette tones, no text",
    "family picnic in green park, golden afternoon sunlight, candid joy, no text",
    "couple cooking together in bright modern kitchen, warm domestic scene, no text",
    "husband and wife sitting on hillside overlooking city at dusk, aspirational, no text",
    "couple laughing over meal at outdoor cafe, warm evening light, bokeh, no text",
    "parents and child playing at park, golden hour, candid joy, no text",
    "couple high-fiving after achievement, warm celebratory mood, no text",
    # Aspirational lifestyle
    "serene morning coffee by large window, city skyline, calm and free, warm light, no text",
    "open laptop on cafe table, person looking pensively out window, morning light, no text",
    "cosy home office with plants and natural light, productive calm, warm tones, no text",
    "person journaling in quiet sunlit cafe, warm amber tones, contemplative, no text",
    "sunrise view from Singapore apartment balcony, aspirational city glow, no text",
    "travel — couple at airport departure, adventure, warm tones, excitement, no text",
    # Freedom & time
    "couple running freely on open coastal road, wide sky, morning light, no text",
    "family at weekend market, vibrant fresh produce, community warmth, no text",
    "quiet weekend morning, couple reading together, warm blankets, no hustle, no text",
    "two people celebrating over dinner, warm restaurant ambience, joy, no text",
    # Filipino cultural warmth
    "tropical garden in warm golden sunlight, lush greenery, serene, no text",
    "warm sunset silhouette over sea, couple watching together, golden tones, no text",
    "urban Singapore skyline at dusk, warm city glow, skyline beauty, no text",
    "outdoor dinner table with warm string lights, family gathering, festive, no text",
    # Professional calm
    "confident professional at bright desk by window, city view, calm and focused, no text",
    "two professionals collaborating, warm modern office, natural light, no text",
    "person deep in thought at desk, warm light, serious but calm, no text",
]


def _load_font(paths: list, size: int) -> ImageFont.FreeTypeFont:
    """Identical to your image_generator.py font loader."""
    for path in paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    win = os.path.join(os.environ.get("WINDIR", ""), "Fonts")
    for path in paths:
        full = os.path.join(win, path)
        if os.path.exists(full):
            try:
                return ImageFont.truetype(full, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _build_prompt(post_text: str) -> str:
    """Rotate through lifestyle styles — same hash approach as your image_generator.py."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    seed = int(hashlib.md5((date_str + post_text[:30]).encode()).hexdigest(), 16)
    style = STYLE_POOL[seed % len(STYLE_POOL)]
    return f"{style}, high resolution, photorealistic, vibrant, warm cinematic tones"


def _hf_call(prompt: str, api_url: str) -> Image.Image | None:
    """Identical to your image_generator.py HuggingFace caller."""
    if not HF_API_TOKEN:
        return None
    w = (min(IMAGE_WIDTH, 1024) // 8) * 8
    h = (min(IMAGE_HEIGHT, 1024) // 8) * 8
    try:
        resp = requests.post(
            api_url,
            headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
            json={"inputs": prompt, "parameters": {
                "width": w, "height": h, "num_inference_steps": 30, "guidance_scale": 7.5,
            }},
            timeout=120,
        )
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content)).convert("RGB")
            return img.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.LANCZOS)
        if resp.status_code == 503:
            print("  ⏳ HF model loading, waiting 25s...")
            time.sleep(25)
            resp2 = requests.post(api_url, headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
                                  json={"inputs": prompt}, timeout=120)
            if resp2.status_code == 200:
                img = Image.open(BytesIO(resp2.content)).convert("RGB")
                return img.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.LANCZOS)
        print(f"  ⚠️ HF HTTP {resp.status_code}")
    except Exception as e:
        print(f"  ❌ HF error: {e}")
    return None


def _pollinations(prompt: str) -> Image.Image | None:
    """Identical to your image_generator.py Pollinations caller."""
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}"
    params = {
        "width": IMAGE_WIDTH, "height": IMAGE_HEIGHT,
        "nologo": "true", "enhance": "true",
        "seed": str(int(time.time()) % 99999), "model": "flux",
    }
    for attempt in range(1, 3):
        try:
            print(f"  🎨 Pollinations attempt {attempt}/2...")
            resp = requests.get(url, params=params, timeout=90)
            if resp.status_code == 200:
                img = Image.open(BytesIO(resp.content)).convert("RGB")
                return img.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.LANCZOS)
            print(f"  ⚠️ Pollinations HTTP {resp.status_code}")
        except requests.exceptions.ReadTimeout:
            print(f"  ⏱️ Pollinations timeout attempt {attempt}...")
        except Exception as e:
            print(f"  ❌ Pollinations error: {e}")
        time.sleep(5)
    return None


def generate_background(prompt: str) -> Image.Image | None:
    """HuggingFace SDXL → SD 2.1 → Pollinations → None."""
    print("  🤗 Trying HuggingFace SDXL...")
    img = _hf_call(prompt, HF_SDXL)
    if img:
        print(f"  ✅ SDXL image ({img.size[0]}x{img.size[1]}px)")
        return img

    print("  🤗 Trying HuggingFace SD 2.1...")
    img = _hf_call(SAFE_PROMPT, HF_SD21)
    if img:
        print(f"  ✅ SD 2.1 image ({img.size[0]}x{img.size[1]}px)")
        return img

    print("  🎨 Trying Pollinations...")
    img = _pollinations(SAFE_PROMPT)
    if img:
        print(f"  ✅ Pollinations image ({img.size[0]}x{img.size[1]}px)")
        return img

    print("  ❌ All image providers failed.")
    return None


def _gradient_overlay(image: Image.Image) -> Image.Image:
    """Dark gradient at bottom — identical logic to your image_generator.py."""
    rgba = image.convert("RGBA")
    overlay = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = rgba.size
    grad_h = int(h * 0.58)
    for i in range(grad_h):
        alpha = int(195 * (i / grad_h))
        y = h - grad_h + i
        draw.rectangle([(0, y), (w, y + 1)], fill=(0, 0, 0, alpha))
    return Image.alpha_composite(rgba, overlay)


def _wrap_text(draw, text: str, font, max_width: int) -> list[str]:
    """Identical word-wrap to your image_generator.py."""
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


def add_text_overlay(image: Image.Image, post_text: str) -> Image.Image:
    """
    Overlay post text on image.
    Gold badge top-left (not red like health news).
    Bold white text bottom area.
    Page handle watermark bottom-right.
    """
    image = _gradient_overlay(image)
    draw  = ImageDraw.Draw(image)
    w, h  = image.size
    pad   = 50

    font_tag      = _load_font(FONT_BOLD, 26)
    font_headline = _load_font(FONT_BOLD, 54)
    font_handle   = _load_font(FONT_REGULAR, 22)

    # ── Gold tag badge (top-left) ─────────────────────────────────────────────
    tag_text = f"  {IMAGE_TAG}  "
    tag_bbox = draw.textbbox((0, 0), tag_text, font=font_tag)
    tag_w = tag_bbox[2] - tag_bbox[0] + 16
    tag_h = tag_bbox[3] - tag_bbox[1] + 12
    draw.rounded_rectangle(
        [(pad, pad), (pad + tag_w, pad + tag_h)],
        radius=6, fill=(*IMAGE_TAG_COLOR, 220),
    )
    draw.text((pad + 8, pad + 6), tag_text, font=font_tag, fill=(255, 255, 255))

    # ── Bold white headline (bottom area) ─────────────────────────────────────
    max_w = w - pad * 2
    lines = _wrap_text(draw, post_text, font_headline, max_w)
    line_h = 68
    handle_gap = 36
    total_h = len(lines) * line_h + handle_gap
    y = h - pad - total_h

    for line in lines:
        draw.text((pad + 2, y + 2), line, font=font_headline, fill=(0, 0, 0, 180))  # shadow
        draw.text((pad, y), line, font=font_headline, fill=(255, 255, 255))
        y += line_h

    # ── Page handle watermark (bottom-right) ──────────────────────────────────
    handle_bbox = draw.textbbox((0, 0), PAGE_HANDLE, font=font_handle)
    handle_w = handle_bbox[2] - handle_bbox[0]
    draw.text(
        (w - pad - handle_w, h - pad - 24),
        PAGE_HANDLE, font=font_handle, fill=(210, 210, 210, 160),
    )

    return image.convert("RGB")


def create_post_image(post_text: str, output_path: str, use_text_card: bool = False) -> str | None:
    """
    Full pipeline: build prompt → generate background → overlay text → save.
    If use_text_card=True, skips image generation entirely — pure black card.
    Returns saved path or None on failure.
    """
    if use_text_card:
        return create_text_card(post_text, output_path)

    print(f'\n📸 Creating LP image: "{post_text[:55]}..."')
    prompt = _build_prompt(post_text)
    bg = generate_background(prompt)

    if bg is None:
        print("  ⚠️ Image generation failed — falling back to text card.")
        return create_text_card(post_text, output_path)

    final = add_text_overlay(bg, post_text)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    final.save(output_path, quality=92)
    print(f"  💾 Saved → {output_path}")
    return output_path


def create_text_card(post_text: str, output_path: str) -> str | None:
    """
    Pure black background with bold white text — MBM viral post style.
    No AI image generation needed. Fast, reliable, high-performing for
    short punchy posts (Format A Pain Point, Format B Couple Humor).
    """
    print(f'\n🃏 Creating text card: "{post_text[:55]}..."')

    img  = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    w, h = img.size
    pad  = 70

    font_tag      = _load_font(FONT_BOLD, 26)
    font_headline = _load_font(FONT_BOLD, 58)
    font_handle   = _load_font(FONT_REGULAR, 22)

    # Gold tag badge top-left
    tag_text = f"  {IMAGE_TAG}  "
    tag_bbox = draw.textbbox((0, 0), tag_text, font=font_tag)
    tag_w = tag_bbox[2] - tag_bbox[0] + 16
    tag_h = tag_bbox[3] - tag_bbox[1] + 12
    draw.rounded_rectangle(
        [(pad, pad), (pad + tag_w, pad + tag_h)],
        radius=6, fill=(*IMAGE_TAG_COLOR, 255),
    )
    draw.text((pad + 8, pad + 6), tag_text, font=font_tag, fill=(255, 255, 255))

    # Bold white text — vertically centered in lower 60% of card
    max_w = w - pad * 2
    lines = _wrap_text(draw, post_text, font_headline, max_w)
    line_h = 72
    total_text_h = len(lines) * line_h
    y = (h - total_text_h) // 2 + 30  # slightly below center

    for line in lines:
        draw.text((pad, y), line, font=font_headline, fill=(255, 255, 255))
        y += line_h

    # Page handle watermark bottom-right
    handle_bbox = draw.textbbox((0, 0), PAGE_HANDLE, font=font_handle)
    handle_w = handle_bbox[2] - handle_bbox[0]
    draw.text(
        (w - pad - handle_w, h - pad - 24),
        PAGE_HANDLE, font=font_handle, fill=(130, 130, 130),
    )

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    img.save(output_path, quality=95)
    print(f"  💾 Text card saved → {output_path}")
    return output_path
