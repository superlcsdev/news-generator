"""
image_generator.py
Generates Facebook post images using Pollinations.ai (free, no API key needed)
- AI generates the background visual
- Pillow overlays the headline text cleanly on top
- Falls back to Hugging Face if Pollinations fails (set HF_API_TOKEN in .env)
"""

import requests
import time
import os
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
IMAGE_WIDTH  = 1200
IMAGE_HEIGHT = 630   # Facebook link-post landscape ratio (1.91:1)
TIMEOUT_SECS = 120
MAX_RETRIES  = 3

HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")

# Primary HF model — SDXL (best quality)
HF_API_URL_PRIMARY  = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
# Secondary HF model — SD 2.1 (faster, more reliable fallback)
HF_API_URL_FALLBACK = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-2-1"

SAFE_PROMPT = (
    "vibrant fresh healthy food flatlay, fruits vegetables superfoods, "
    "bright natural lighting, professional photography, no text, no words"
)

# Font paths to try (Windows → Linux fallbacks)
FONT_PATHS_BOLD = [
    "arialbd.ttf",
    "Arial_Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
FONT_PATHS_REGULAR = [
    "arial.ttf",
    "Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]


def _load_font(paths: list, size: int) -> ImageFont.FreeTypeFont:
    """Try each font path; fall back to Pillow default if none found."""
    for path in paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    win_fonts = os.path.join(os.environ.get("WINDIR", ""), "Fonts")
    for path in paths:
        full = os.path.join(win_fonts, path)
        if os.path.exists(full):
            try:
                return ImageFont.truetype(full, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _build_prompt(headline: str, category: str = "health") -> str:
    """
    Build a Pollinations prompt with high visual variety.
    Uses a pool of 32 distinct visual styles, rotating by date + headline
    so consecutive posts always look different.
    """
    import hashlib
    from datetime import datetime

    STYLE_POOL = [
        # Food & nutrition
        "vibrant fresh fruit bowl flatlay, tropical colours, top-down view, bright natural light, no text",
        "colourful smoothie bowls and superfoods on white marble, clean minimal aesthetic, no text",
        "fresh vegetables at market, vivid greens and reds, rustic wooden background, no text",
        "close-up macro shot of fresh herbs and spices, bokeh background, warm golden tones, no text",
        "healthy meal prep containers, clean organised layout, bright kitchen setting, no text",
        "exotic tropical fruits sliced open, vibrant saturated colours, overhead shot, no text",
        "fresh salad greens with water droplets, macro photography, vivid colours, no text",
        "wholesome breakfast spread, warm morning light, cosy kitchen atmosphere, no text",
        # Nature & wellness
        "serene forest path at dawn, soft morning mist, green light through trees, peaceful, no text",
        "ocean sunrise over calm water, warm golden hour light, horizon view, no text",
        "lush green rainforest waterfall, fresh and vibrant, nature photography, no text",
        "wildflower meadow in soft sunlight, bokeh background, warm pastel tones, no text",
        "mountain lake reflection at sunrise, crisp clean air, stunning landscape, no text",
        "zen garden with smooth stones and bamboo, peaceful minimalist, soft natural light, no text",
        "dewy leaves in morning light, macro nature photography, ethereal beauty, no text",
        "cherry blossom branch against blue sky, soft pink tones, spring freshness, no text",
        # Active lifestyle
        "yoga on cliff overlooking ocean at sunrise, silhouette, inspiring, no text",
        "morning run in city park, golden hour light, motion blur, energetic, no text",
        "cycling through autumn forest path, warm golden leaves, dynamic motion, no text",
        "swimming pool lane view, clear blue water, clean lines, healthy lifestyle, no text",
        "hiking boots on mountain trail, adventure lifestyle, rugged nature, no text",
        # Mindfulness & calm
        "hands holding warm cup of tea, cosy morning light, soft shallow depth of field, no text",
        "candle flame close-up, warm amber tones, soft bokeh, calm and peaceful, no text",
        "open book beside window with rain, cosy interior, warm light, peaceful mood, no text",
        "meditation stones balanced on calm water, zen minimalist, pastel tones, no text",
        "soft sunrise light through curtains, peaceful morning awakening, warm tones, no text",
        # Science & medical
        "abstract blue teal medical science background, clean lines, professional, no text",
        "DNA helix abstract visualization, blue glowing tones, modern science, no text",
        "clean laboratory glassware with colourful liquids, professional research, no text",
        # Lifestyle
        "happy healthy people outdoors, warm sunlight, candid lifestyle photography, no text",
        "farmer's market fresh produce, vibrant colours, community atmosphere, no text",
        "aerial view of green parks, fresh urban greenery, top-down perspective, no text",
    ]

    # Rotate by date + headline so every post gets a different style
    date_str  = datetime.now().strftime("%Y-%m-%d")
    hash_seed = int(hashlib.md5((date_str + headline[:30]).encode()).hexdigest(), 16)
    style     = STYLE_POOL[hash_seed % len(STYLE_POOL)]

    return f"{style}, high resolution, photorealistic, vibrant"


def _call_huggingface(prompt: str, width: int, height: int, api_url: str):
    """Call a single HuggingFace model endpoint. Returns Image or None."""
    if not HF_API_TOKEN:
        return None
    try:
        resp = requests.post(
            api_url,
            headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
            json={
                "inputs": prompt,
                "parameters": {
                    "width":               min(width, 1024),
                    "height":              min(height, 1024),
                    "num_inference_steps": 30,
                    "guidance_scale":      7.5,
                }
            },
            timeout=120,
        )
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content)).convert("RGB")
            img = img.resize((width, height), Image.LANCZOS)
            return img
        elif resp.status_code == 503:
            # Model loading — wait and retry once
            print(f"  ⏳ HF model loading, waiting 25s...")
            time.sleep(25)
            resp = requests.post(
                api_url,
                headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
                json={"inputs": prompt},
                timeout=120,
            )
            if resp.status_code == 200:
                img = Image.open(BytesIO(resp.content)).convert("RGB")
                img = img.resize((width, height), Image.LANCZOS)
                return img
        print(f"  ⚠️  HF HTTP {resp.status_code}: {resp.text[:150]}")
        return None
    except Exception as e:
        print(f"  ❌ HF error: {e}")
        return None


def _generate_via_huggingface(prompt: str, width: int, height: int):
    """Try SDXL first, fall back to SD 2.1."""
    if not HF_API_TOKEN:
        print("  ⚠️  HF_API_TOKEN not set — skipping HuggingFace.")
        return None

    print("  🤗 Trying HuggingFace SDXL (primary)...")
    img = _call_huggingface(prompt, width, height, HF_API_URL_PRIMARY)
    if img:
        print(f"  ✅ SDXL image received ({img.size[0]}x{img.size[1]}px)")
        return img

    print("  🤗 Trying HuggingFace SD 2.1 (secondary)...")
    img = _call_huggingface(prompt, width, height, HF_API_URL_FALLBACK)
    if img:
        print(f"  ✅ SD 2.1 image received ({img.size[0]}x{img.size[1]}px)")
        return img

    print("  ❌ Both HuggingFace models failed.")
    return None


def _generate_via_pollinations(prompt: str, width: int, height: int):
    """Last resort — try Pollinations new endpoint."""
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}"
    params = {
        "width":   width,
        "height":  height,
        "nologo":  "true",
        "enhance": "true",
        "seed":    str(int(time.time()) % 99999),
        "model":   "flux",   # flux model is more stable than default
    }
    for attempt in range(1, 3):
        try:
            print(f"  🎨 Pollinations attempt {attempt}/2...")
            resp = requests.get(url, params=params, timeout=90)
            if resp.status_code == 200:
                img = Image.open(BytesIO(resp.content)).convert("RGB")
                print(f"  ✅ Pollinations image received ({img.size[0]}x{img.size[1]}px)")
                return img
            print(f"  ⚠️  Pollinations HTTP {resp.status_code}, retrying...")
        except requests.exceptions.ReadTimeout:
            print(f"  ⏱️  Pollinations timeout on attempt {attempt}...")
        except Exception as e:
            print(f"  ❌ Pollinations error: {e}")
        time.sleep(5)
    return None


def generate_background(prompt: str, width: int = IMAGE_WIDTH, height: int = IMAGE_HEIGHT):
    """
    Generate background image.
    Priority: HuggingFace SDXL → HuggingFace SD 2.1 → Pollinations → None
    """
    # ── 1. Try HuggingFace (primary + secondary) ──────────────────
    img = _generate_via_huggingface(prompt, width, height)
    if img:
        return img

    # ── 2. Try HuggingFace with safe prompt if original failed ────
    if prompt != SAFE_PROMPT:
        print("  ⚠️  Retrying HuggingFace with safe generic prompt...")
        img = _generate_via_huggingface(SAFE_PROMPT, width, height)
        if img:
            return img

    # ── 3. Last resort: Pollinations ──────────────────────────────
    print("  ⚠️  HuggingFace failed — trying Pollinations as last resort...")
    img = _generate_via_pollinations(SAFE_PROMPT, width, height)
    if img:
        return img

    print("  ❌ All image generation methods failed.")
    return None


def _draw_gradient_overlay(image: Image.Image) -> Image.Image:
    """Add a dark gradient at the bottom so text is always readable."""
    img_rgba = image.convert("RGBA")
    overlay  = Image.new("RGBA", img_rgba.size, (0, 0, 0, 0))
    draw     = ImageDraw.Draw(overlay)
    w, h     = img_rgba.size
    grad_h   = int(h * 0.55)

    for i in range(grad_h):
        alpha = int(195 * (i / grad_h))
        y = h - grad_h + i
        draw.rectangle([(0, y), (w, y + 1)], fill=(0, 0, 0, alpha))

    return Image.alpha_composite(img_rgba, overlay)


def _wrap_text(draw, text: str, font, max_width: int) -> list:
    """Word-wrap text to fit within max_width pixels."""
    words   = text.split()
    lines   = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] > max_width and current:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def add_text_overlay(
    image:    Image.Image,
    headline: str,
    source:   str = "",
    tag:      str = "HEALTH NEWS",
) -> Image.Image:
    """Overlay headline + optional source/tag onto the background image."""
    image = _draw_gradient_overlay(image)
    draw  = ImageDraw.Draw(image)
    w, h  = image.size
    pad   = 50

    font_tag      = _load_font(FONT_PATHS_BOLD,    28)
    font_headline = _load_font(FONT_PATHS_BOLD,    58)
    font_source   = _load_font(FONT_PATHS_REGULAR, 30)

    # ── TAG badge (top-left) ──────────────────────────────────────────────────
    tag_text = f"  {tag}  "
    tag_bbox = draw.textbbox((0, 0), tag_text, font=font_tag)
    tag_w    = tag_bbox[2] - tag_bbox[0] + 20
    tag_h    = tag_bbox[3] - tag_bbox[1] + 14
    draw.rounded_rectangle(
        [(pad, pad), (pad + tag_w, pad + tag_h)],
        radius=6, fill=(220, 50, 50, 220)
    )
    draw.text((pad + 10, pad + 7), tag_text, font=font_tag, fill=(255, 255, 255))

    # ── Headline (bottom area) ────────────────────────────────────────────────
    max_text_w  = w - pad * 2
    lines       = _wrap_text(draw, headline, font_headline, max_text_w)
    line_height = 70
    total_h     = len(lines) * line_height + (50 if source else 0)
    y           = h - pad - total_h

    for line in lines:
        draw.text((pad + 2, y + 2), line, font=font_headline, fill=(0, 0, 0, 180))
        draw.text((pad,     y),     line, font=font_headline, fill=(255, 255, 255))
        y += line_height

    # ── Source label (below headline) ─────────────────────────────────────────
    if source:
        draw.text((pad + 1, y + 1), source, font=font_source, fill=(0, 0, 0, 160))
        draw.text((pad,     y),     source, font=font_source, fill=(200, 200, 200))

    return image.convert("RGB")


def create_post_image(
    headline:       str,
    output_path:    str,
    category:       str   = "health",
    source:         str   = "",
    tag:            str   = "HEALTH NEWS",
    fallback_color: tuple = (20, 90, 60),
):
    """Full pipeline: generate background → overlay text → save file."""
    print(f"\n📸 Creating image for: \"{headline[:60]}...\"")

    prompt = _build_prompt(headline, category)
    bg     = generate_background(prompt)

    if bg is None:
        print("  ⚠️  Using solid colour fallback background.")
        bg = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT), fallback_color)

    final = add_text_overlay(bg, headline, source=source, tag=tag)
    final.save(output_path, quality=92)
    print(f"  💾 Saved → {output_path}")
    return output_path


# ── CLI test ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_cases = [
        {
            "headline": "5 Superfoods That Dramatically Boost Your Immune System This Winter",
            "category": "health",
            "source":   "healthline.com",
            "output":   "test_health.jpg",
        },
        {
            "headline": "New Study Reveals How Daily Walking Reduces Heart Disease Risk by 35%",
            "category": "fitness",
            "source":   "medicalnewstoday.com",
            "output":   "test_fitness.jpg",
        },
    ]

    for tc in test_cases:
        create_post_image(
            headline    = tc["headline"],
            output_path = tc["output"],
            category    = tc["category"],
            source      = tc["source"],
        )
