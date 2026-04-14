"""
image_generator.py — news-generator (health posts)
Format : 1080x1080 square
Pipeline:
  1. HuggingFace SDXL-Lightning  (fast, free with token)
  2. HuggingFace SD 1.5          (reliable fallback)
  3. Local stock image            (stock/health/ folder)
  4. Dark card (30,30,30)         (absolute last resort)
Branding: LAWRENCE SIA / YOUR PERSONAL COACH
Font    : Montserrat (fonts/ folder) → Liberation/DejaVu fallback
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

IMAGE_WIDTH  = 1080
IMAGE_HEIGHT = 1080

HF_API_TOKEN      = os.getenv("HF_API_TOKEN", "")
HF_SDXL_LIGHTNING = "https://router.huggingface.co/hf-inference/models/ByteDance/SDXL-Lightning"
HF_SD15           = "https://router.huggingface.co/hf-inference/models/stable-diffusion-v1-5/stable-diffusion-v1-5"

SAFE_PROMPT = (
    "vibrant fresh healthy food flatlay, fruits vegetables superfoods, "
    "bright natural lighting, professional photography, square composition, no text, no words"
)

_BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
STOCK_DIR  = os.path.join(_BASE_DIR, "stock", "health")
_FONTS_DIR = os.path.join(_BASE_DIR, "fonts")

FONT_EXTRABOLD = [
    os.path.join(_FONTS_DIR, "Montserrat-ExtraBold.ttf"),
    os.path.join(_FONTS_DIR, "Montserrat-Bold.ttf"),
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
FONT_BOLD = [
    os.path.join(_FONTS_DIR, "Montserrat-Bold.ttf"),
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
FONT_MEDIUM = [
    os.path.join(_FONTS_DIR, "Montserrat-Medium.ttf"),
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ── Image prompt generator ─────────────────────────────────────────────────────
# Gemini reads the actual headline and writes a specific, vivid image prompt.
# This is what makes each image unique and related to the actual news story.

IMAGE_PROMPT_REQUEST = """You are a creative director for a health news Facebook page.
Write ONE image generation prompt for this article headline.

Headline: "{headline}"

RULES:
- The image must be DIRECTLY related to the topic in the headline
- Be specific and visual — describe what you actually see in the image
- Avoid generic laptop/desk/phone setups unless the article is literally about devices
- Use varied visual styles: macro photography, aerial shots, candid moments, abstract concepts, clinical settings, nature scenes
- No text, no words, no letters in the image
- Always end with: "square composition, 1080x1080, photorealistic, high resolution, no text, no words"
- Max 20 words total in the prompt

Examples of GOOD prompts for health headlines:
- "Researchers Discover New Gut Bacteria Link to Mental Health" → "colorful gut microbiome illustration, glowing bacteria clusters, teal and purple tones, scientific abstract visualization"
- "Study: 20 Minutes of Exercise Reduces Anxiety by 40%" → "woman running on coastal path at sunrise, motion blur, energetic, cool morning light"
- "Singapore Nurses at Risk of Burnout, Study Finds" → "exhausted nurse in hospital corridor, dim fluorescent light, realistic, candid"
- "New Vaccine Shows 90% Effectiveness Against Flu Strain" → "close-up syringe with glowing liquid, clean clinical white background, sharp focus"
- "Lack of Sleep Shrinks Brain Volume, Research Shows" → "brain scan MRI cross-section, glowing blue medical imaging, dark background, clinical"

Write ONLY the image prompt. No preamble. No explanation."""

# Fallback style pool — used when Gemini is unavailable
# Intentionally diverse: cool tones, warm tones, clinical, nature, abstract
STYLE_POOL = [
    # Clinical / medical
    "stethoscope on white surface, shallow depth of field, clean clinical lighting, square, no text",
    "close-up of pills and capsules in vibrant colours, macro, white background, square, no text",
    "hospital corridor with soft blue light, perspective view, clean modern, square, no text",
    "doctor hands holding clipboard, blurred clinical background, professional, square, no text",
    "blood pressure monitor on white desk, clinical precision, cool tones, square, no text",
    "close-up syringe with clear liquid, clean white clinical background, sharp focus, square, no text",
    # Science / research
    "DNA helix glowing blue abstract visualization, dark background, modern science, square, no text",
    "colourful brain scan MRI cross-section, glowing medical imaging, dark background, square, no text",
    "microscope slide with cells glowing green, scientific macro, dark background, square, no text",
    "laboratory test tubes in rack, vivid coloured liquids, clean research, square, no text",
    "scientist hands in blue gloves holding petri dish, cool clinical tones, square, no text",
    # Active lifestyle
    "runner on coastal path at sunrise, motion blur, cool morning light, energetic, square, no text",
    "yoga pose on cliff at sunrise, dramatic silhouette, blue sky, square, no text",
    "swimmer in pool, underwater shot, blue light refraction, athletic, square, no text",
    "cyclist on mountain road, dramatic landscape, cool morning fog, square, no text",
    "person meditating in green park, soft morning light, peaceful, square, no text",
    # Food / nutrition
    "vibrant açaí bowl with fresh berries, top-down, bright cool tones, square, no text",
    "fresh green smoothie in glass, condensation droplets, white background, square, no text",
    "colourful vegetable stir-fry in wok, steam rising, vivid reds and greens, square, no text",
    "dark chocolate squares with fruit, artistic flatlay, moody lighting, square, no text",
    # Mental health / sleep
    "person sleeping in dark room, soft blue moonlight through curtains, peaceful, square, no text",
    "person sitting by window looking out at rain, contemplative, cool blue tones, square, no text",
    "abstract brain with colourful neural connections glowing, dark background, square, no text",
    "hands holding coffee cup in morning light, calm and still, muted tones, square, no text",
    # Nature / wellness
    "lush green forest trail with mist, cool morning light, peaceful depth, square, no text",
    "ocean waves crashing on rocks, long exposure, moody dramatic sky, square, no text",
    "mountain peak above clouds at sunrise, dramatic perspective, square, no text",
    "cherry blossom branch, soft pink against pure white sky, minimalist, square, no text",
    # Professional context
    "nurse in scrubs in hospital garden break, natural light, candid, square, no text",
    "pharmacist examining medicine bottle, professional, clean pharmacy background, square, no text",
    "surgeon hands in green gloves, operating theatre, dramatic lighting, square, no text",
    "engineer doing physical safety check, industrial setting, professional, square, no text",
]


def _load_font(paths: list, size: int) -> ImageFont.FreeTypeFont:
    for path in paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _build_prompt_via_gemini(headline: str) -> str | None:
    """Ask Gemini to write a specific image prompt based on the actual headline."""
    if not GEMINI_API_KEY:
        return None
    try:
        prompt = IMAGE_PROMPT_REQUEST.format(headline=headline)
        resp   = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=15,
        )
        result = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        # Make sure it has the required suffix
        if "no text" not in result.lower():
            result += ", square composition, photorealistic, high resolution, no text, no words"
        print(f"  🎨 Gemini image prompt: {result[:80]}...")
        return result
    except Exception as e:
        print(f"  ⚠️  Gemini image prompt error: {e}")
        return None


def _build_prompt(headline: str) -> str:
    """Try Gemini first for a headline-specific prompt, fall back to style pool."""
    gemini_prompt = _build_prompt_via_gemini(headline)
    if gemini_prompt:
        return gemini_prompt
    # Fallback: rotate through diverse style pool
    date_str  = datetime.now().strftime("%Y-%m-%d")
    hash_seed = int(hashlib.md5((date_str + headline[:30]).encode()).hexdigest(), 16)
    style     = STYLE_POOL[hash_seed % len(STYLE_POOL)]
    print(f"  🎨 Fallback style: {style[:60]}...")
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


def _hf_call(prompt: str, api_url: str) -> Image.Image | None:
    if not HF_API_TOKEN:
        return None
    w = (min(IMAGE_WIDTH,  1024) // 8) * 8
    h = (min(IMAGE_HEIGHT, 1024) // 8) * 8
    try:
        resp = requests.post(
            api_url,
            headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
            json={"inputs": prompt, "parameters": {
                "width": w, "height": h,
                "num_inference_steps": 4,
                "guidance_scale": 0,
            }},
            timeout=120,
        )
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content)).convert("RGB")
            return img.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.LANCZOS)
        if resp.status_code == 503:
            print("  ⏳ HF model loading, waiting 20s...")
            time.sleep(20)
            resp2 = requests.post(api_url,
                headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
                json={"inputs": prompt}, timeout=120)
            if resp2.status_code == 200:
                img = Image.open(BytesIO(resp2.content)).convert("RGB")
                return img.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.LANCZOS)
        print(f"  ⚠️  HF HTTP {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        print(f"  ⚠️  HF error: {e}")
    return None


def _stock_image(headline: str) -> Image.Image | None:
    """Pick a stock photo from stock/health/ rotating by date+headline hash."""
    if not os.path.isdir(STOCK_DIR):
        return None
    files = sorted([f for f in os.listdir(STOCK_DIR)
                    if f.lower().endswith((".jpg", ".jpeg", ".png"))])
    if not files:
        return None
    date_str  = datetime.now().strftime("%Y-%m-%d")
    hash_seed = int(hashlib.md5((date_str + headline[:20]).encode()).hexdigest(), 16)
    chosen    = files[hash_seed % len(files)]
    try:
        img = Image.open(os.path.join(STOCK_DIR, chosen)).convert("RGB")
        img = img.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.LANCZOS)
        print(f"  🖼️  Stock image: {chosen}")
        return img
    except Exception as e:
        print(f"  ⚠️  Stock image error: {e}")
    return None


def generate_background(prompt: str, headline: str = "") -> Image.Image | None:
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

    print("  ⚠️  HF failed — trying stock image...")
    img = _stock_image(headline)
    if img:
        return img

    print("  ❌ All providers failed.")
    return None


def _draw_logo_bar(draw, w: int, y_top: int, bar_h: int = 56) -> None:
    draw.rectangle([(0, y_top), (w, y_top + bar_h)], fill=(12, 12, 16, 220))
    fb = _load_font(FONT_BOLD,   20)
    fs = _load_font(FONT_MEDIUM, 11)
    bt = "LAWRENCE SIA"
    st = "YOUR PERSONAL COACH"
    bb = draw.textbbox((0, 0), bt, font=fb)
    sb = draw.textbbox((0, 0), st, font=fs)
    draw.text(((w - (bb[2]-bb[0])) // 2, y_top + 7),  bt, font=fb, fill=(255, 255, 255))
    draw.text(((w - (sb[2]-sb[0])) // 2, y_top + 33), st, font=fs, fill=(155, 155, 155))
    draw.rectangle([(0, y_top), (w, y_top + 2)], fill=(180, 120, 40))


def add_text_overlay(image: Image.Image, headline: str, tag: str = "HEALTH NEWS") -> Image.Image:
    w, h       = image.size
    SIDE_PAD   = 50
    BOTTOM_PAD = 36
    LOGO_BAR_H = 56
    CAP_GAP    = 16

    font      = _load_font(FONT_EXTRABOLD, 54)
    temp_draw = ImageDraw.Draw(image)
    max_w     = w - SIDE_PAD * 2

    def pw(text, fnt, mx):
        words, lines, cur = text.split(), [], ""
        for word in words:
            test = f"{cur} {word}".strip()
            if temp_draw.textbbox((0, 0), test, font=fnt)[2] > mx and cur:
                lines.append(cur); cur = word
            else:
                cur = test
        if cur: lines.append(cur)
        return lines

    lines = pw(headline, font, max_w)
    if len(lines) > 2: font = _load_font(FONT_EXTRABOLD, 44); lines = pw(headline, font, max_w)
    if len(lines) > 3: font = _load_font(FONT_EXTRABOLD, 36); lines = pw(headline, font, max_w)

    line_h      = int(font.size * 1.28)
    total_cap_h = len(lines) * line_h
    cap_y_start = h - BOTTOM_PAD - total_cap_h
    logo_y_top  = cap_y_start - CAP_GAP - LOGO_BAR_H
    grad_h      = (h - logo_y_top) + 60

    rgba    = image.convert("RGBA")
    overlay = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    od      = ImageDraw.Draw(overlay)
    for i in range(grad_h):
        od.rectangle([(0, h - grad_h + i), (w, h - grad_h + i + 1)],
                     fill=(0, 0, 0, int(240 * i / grad_h)))
    image = Image.alpha_composite(rgba, overlay).convert("RGB")
    draw  = ImageDraw.Draw(image)

    font_tag = _load_font(FONT_BOLD, 22)
    tag_text = f"  {tag}  "
    tb       = draw.textbbox((0, 0), tag_text, font=font_tag)
    tw, th   = tb[2]-tb[0]+20, tb[3]-tb[1]+14
    draw.rounded_rectangle([(SIDE_PAD, SIDE_PAD), (SIDE_PAD+tw, SIDE_PAD+th)],
                           radius=6, fill=(220, 50, 50, 220))
    draw.text((SIDE_PAD+10, SIDE_PAD+7), tag_text, font=font_tag, fill=(255, 255, 255))

    _draw_logo_bar(draw, w, logo_y_top, LOGO_BAR_H)

    y = cap_y_start
    for line in lines:
        draw.text((SIDE_PAD+2, y+2), line, font=font, fill=(0, 0, 0, 150))
        draw.text((SIDE_PAD,   y),   line, font=font, fill=(255, 255, 255))
        y += line_h

    return image


def _create_dark_card(headline: str, tag: str = "HEALTH NEWS") -> Image.Image:
    img  = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT), (30, 30, 30))
    draw = ImageDraw.Draw(img)
    w, h = img.size
    PAD  = 60
    LBH  = 56

    font_tag = _load_font(FONT_BOLD, 22)
    tag_text = f"  {tag}  "
    tb = draw.textbbox((0, 0), tag_text, font=font_tag)
    tw, th = tb[2]-tb[0]+20, tb[3]-tb[1]+14
    draw.rounded_rectangle([(PAD, PAD), (PAD+tw, PAD+th)], radius=6, fill=(220, 50, 50, 220))
    draw.text((PAD+10, PAD+7), tag_text, font=font_tag, fill=(255, 255, 255))

    lyt = h - 30 - LBH
    _draw_logo_bar(draw, w, lyt, LBH)

    usable_top = PAD + th + 40
    usable_h   = (lyt - 20) - usable_top
    max_w      = w - PAD * 2
    font       = _load_font(FONT_EXTRABOLD, 64)
    lines      = _wrap_text(draw, headline, font, max_w)
    if len(lines) > 3: font = _load_font(FONT_EXTRABOLD, 52); lines = _wrap_text(draw, headline, font, max_w)
    if len(lines) > 4: font = _load_font(FONT_EXTRABOLD, 42); lines = _wrap_text(draw, headline, font, max_w)

    lh = int(font.size * 1.38)
    y  = usable_top + (usable_h - len(lines) * lh) // 2
    for line in lines:
        draw.text((PAD, y), line, font=font, fill=(255, 255, 255))
        y += lh
    return img


def create_post_image(headline: str, output_path: str, category: str = "health",
                      source: str = "", tag: str = "HEALTH NEWS",
                      fallback_color: tuple = (30, 30, 30)) -> str | None:
    print(f'\n📸 Creating image: "{headline[:60]}..."')
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    prompt = _build_prompt(headline)
    bg     = generate_background(prompt, headline=headline)
    final  = add_text_overlay(bg, headline, tag=tag) if bg else _create_dark_card(headline, tag=tag)
    if bg is None:
        print("  ⚠️  Using dark card fallback.")
    final.save(output_path, quality=92)
    print(f"  💾 Saved → {output_path}")
    return output_path


if __name__ == "__main__":
    os.makedirs("output_images", exist_ok=True)
    create_post_image("New Study: Poor Sleep Reduces Professional Performance by 40%",
                      "output_images/test_health.jpg")
