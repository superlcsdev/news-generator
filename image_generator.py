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
HF_API_URL   = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"

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
    """Turn a news headline into a background-image prompt. No text in prompt."""
    category_styles = {
        "health":    "vibrant healthy lifestyle photography, fresh vegetables fruits superfoods, "
                     "bright natural lighting, clean minimal background, professional food/wellness photo",
        "fitness":   "dynamic fitness workout scene, athletic energy, bright studio lighting, "
                     "motivational sports photography, clean background",
        "mental":    "calm serene mindfulness scene, soft pastel tones, peaceful nature, "
                     "meditation wellness aesthetic, soft bokeh background",
        "nutrition": "colorful nutritious meal flatlay, fresh ingredients, professional food photography, "
                     "bright natural lighting, top-down view",
        "medical":   "clean modern medical research background, blue tones, abstract science, "
                     "professional healthcare aesthetic, no people",
    }
    style = category_styles.get(category.lower(), category_styles["health"])
    return f"{style}, high resolution, no text, no words, no letters, photorealistic"


def _generate_via_huggingface(prompt: str, width: int, height: int):
    """Fallback image generation using Hugging Face Inference API."""
    if not HF_API_TOKEN:
        print("  ⚠️  HF_API_TOKEN not set — skipping Hugging Face fallback.")
        return None
    try:
        print("  🤗 Trying Hugging Face fallback...")
        resp = requests.post(
            HF_API_URL,
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
            print(f"  ✅ Hugging Face image received ({img.size[0]}x{img.size[1]}px)")
            return img
        elif resp.status_code == 503:
            print("  ⏳ Hugging Face model loading, waiting 20s...")
            time.sleep(20)
            resp = requests.post(
                HF_API_URL,
                headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
                json={"inputs": prompt},
                timeout=120,
            )
            if resp.status_code == 200:
                img = Image.open(BytesIO(resp.content)).convert("RGB")
                img = img.resize((width, height), Image.LANCZOS)
                print("  ✅ Hugging Face image received on retry.")
                return img
        print(f"  ⚠️  Hugging Face returned HTTP {resp.status_code}: {resp.text[:200]}")
        return None
    except Exception as e:
        print(f"  ❌ Hugging Face error: {e}")
        return None


def generate_background(prompt: str, width: int = IMAGE_WIDTH, height: int = IMAGE_HEIGHT):
    """Try Pollinations first, fall back to Hugging Face, then return None."""
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}"
    params = {
        "width":   width,
        "height":  height,
        "nologo":  "true",
        "enhance": "true",
        "seed":    str(int(time.time()) % 99999),
    }

    # ── Try Pollinations ──────────────────────────────────────────────────────
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"  🎨 Pollinations attempt {attempt}/{MAX_RETRIES}...")
            resp = requests.get(url, params=params, timeout=TIMEOUT_SECS)
            if resp.status_code == 200:
                img = Image.open(BytesIO(resp.content)).convert("RGB")
                print(f"  ✅ Pollinations image received ({img.size[0]}x{img.size[1]}px)")
                return img
            elif resp.status_code == 500 and attempt == 2:
                print("  ⚠️  HTTP 500 — switching to safe generic prompt...")
                url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(SAFE_PROMPT)}"
            else:
                print(f"  ⚠️  HTTP {resp.status_code}, retrying in 5s...")
        except requests.exceptions.ReadTimeout:
            print(f"  ⏱️  Timeout on attempt {attempt}, waiting 5s...")
        except Exception as e:
            print(f"  ❌ Pollinations error: {e}")
        time.sleep(5)

    # ── Try Hugging Face ──────────────────────────────────────────────────────
    print("  ⚠️  Pollinations failed — trying Hugging Face...")
    hf_img = _generate_via_huggingface(SAFE_PROMPT, width, height)
    if hf_img:
        return hf_img

    print("  ❌ All image generation attempts failed.")
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
