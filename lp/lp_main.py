"""
lp/lp_main.py
@lawrenceprecioussia Facebook Automation Orchestrator.

Mirrors the exact pattern from ../main.py — same argparse, same step-by-step
logging, same dry-run flag, same pipeline structure.

Run modes:
  python lp_main.py --type text            → AI quote/wisdom/humor/couple post
  python lp_main.py --type text --format BW → force Format BW (couple+wisdom)
  python lp_main.py --type poll            → AI poll post (text only)
  python lp_main.py --type news            → news article reframed through LP lens
  python lp_main.py --type cta             → rotating pre-written CTA post
  python lp_main.py --type text --dry-run  → generate + print, skip FB post

Env vars (GitHub Secrets):
  GEMINI_API_KEY            — shared with news-generator
  OPENROUTER_API_KEY        — shared with news-generator (optional fallback)
  HF_API_TOKEN              — shared with news-generator (optional)
  FB_LP_PAGE_ID             — lawrenceprecioussia Page ID   ← DIFFERENT from news-generator
  FB_LP_PAGE_ACCESS_TOKEN   — lawrenceprecioussia token     ← DIFFERENT from news-generator
"""

import argparse
import os
import sys
import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load .env from repo root (one level up from lp/)
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# All imports from the lp/ subfolder
from lp_post_generator import generate_text_post, generate_poll_post, generate_news_hook, get_cta_post
from lp_news_fetcher import fetch_top_articles, save_posted_article
from lp_image_generator import create_post_image, create_text_card
from lp_faith_generator import generate_faith_post
from brand_voice import WEEKLY_CALENDAR

# Shared fb_poster from repo root — safe to reuse, uses different env var names
sys.path.insert(0, str(Path(__file__).parent.parent))
from fb_poster import post_to_facebook as _post_image, FB_PAGE_ID as _HEALTH_ID

import requests

OUTPUT_DIR = Path(__file__).parent.parent / "lp_output_images"
OUTPUT_DIR.mkdir(exist_ok=True)

GRAPH_API = "https://graph.facebook.com/v19.0"


# ─────────────────────────────────────────────────────────────────────────────
# LP-SPECIFIC Facebook poster (uses LP secrets, not health page secrets)
# ─────────────────────────────────────────────────────────────────────────────

def _lp_creds() -> tuple[str, str]:
    return (
        os.environ.get("FB_LP_PAGE_ID", ""),
        os.environ.get("FB_LP_PAGE_ACCESS_TOKEN", ""),
    )


def lp_post_image(image_path: str, caption: str, first_comment: str = "") -> bool:
    """Upload image + caption to the LP Facebook page."""
    page_id, token = _lp_creds()
    if not page_id or not token:
        print("  ❌ FB_LP_PAGE_ID or FB_LP_PAGE_ACCESS_TOKEN not set.")
        return False
    try:
        import time
        print("  📤 Uploading image...")
        with open(image_path, "rb") as f:
            up = requests.post(
                f"{GRAPH_API}/{page_id}/photos",
                data={"access_token": token, "published": "false"},
                files={"source": f}, timeout=60,
            )
        ud = up.json()
        if "id" not in ud:
            print(f"  ❌ Upload failed: {ud}"); return False
        photo_id = ud["id"]
        print(f"  ✅ Photo uploaded (id: {photo_id})")

        print("  📢 Publishing post...")
        pr = requests.post(
            f"{GRAPH_API}/{page_id}/feed",
            data={"access_token": token, "message": caption,
                  "attached_media[0]": f'{{"media_fbid":"{photo_id}"}}'},
            timeout=30,
        )
        pd = pr.json()
        if "id" not in pd:
            print(f"  ❌ Post failed: {pd}"); return False
        post_id = pd["id"]
        print(f"  ✅ Posted! ID: {post_id}")

        if first_comment:
            time.sleep(3)
            cr = requests.post(
                f"{GRAPH_API}/{post_id}/comments",
                data={"access_token": token, "message": first_comment}, timeout=15,
            )
            if "id" in cr.json():
                print("  💬 First comment added.")

        return True
    except Exception as e:
        print(f"  ❌ LP Facebook error: {e}"); return False


def lp_post_text(message: str) -> bool:
    """Post plain text to the LP Facebook page (polls, CTA)."""
    page_id, token = _lp_creds()
    if not page_id or not token:
        print("  ❌ FB_LP_PAGE_ID or FB_LP_PAGE_ACCESS_TOKEN not set.")
        return False
    try:
        resp = requests.post(
            f"{GRAPH_API}/{page_id}/feed",
            data={"access_token": token, "message": message}, timeout=30,
        )
        data = resp.json()
        if "id" in data:
            print(f"  ✅ Text post published! ID: {data['id']}"); return True
        print(f"  ❌ Text post failed: {data}"); return False
    except Exception as e:
        print(f"  ❌ LP Facebook error: {e}"); return False


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINES
# ─────────────────────────────────────────────────────────────────────────────

def run_text_post(fmt: str, hook: str, dry_run: bool):
    # Use weekly calendar when format/hook not manually specified
    if fmt == "any" or hook == "any":
        day = datetime.date.today().weekday()
        calendar_entry = WEEKLY_CALENDAR[day]
        if fmt == "any":
            fmt = calendar_entry["format"]
        if hook == "any":
            hook = calendar_entry["hook"]
        print(f"  📅 Calendar: today is {['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][day]} → Format {fmt} | Hook {hook}")

    print("\n[1/4] Generating text post...")
    result = generate_text_post(post_format=fmt, hook=hook)
    print(f"\n  POST:    {result['post']}")
    print(f"  CAPTION: {result['caption']}")
    print(f"  IMG HOOK: {result.get('image_hook', '(none)')}")
    print(f"  FORMAT:  {result['format']} | HOOK: {result['hook']}")

    # Use pure black text card for short punchy formats (A and B)
    # Use photo background for wisdom/story formats (BW, D, E)
    use_text_card = fmt in ("A", "B")

    print(f"\n[2/4] {'Creating text card' if use_text_card else 'Generating image'}...")
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    img_path = str(OUTPUT_DIR / f"lp_post_{ts}.jpg")
    # Image always shows the short hook — full story goes in FB caption
    image_text = result.get("image_hook") or result["post"]
    saved = create_post_image(post_text=image_text, output_path=img_path, use_text_card=use_text_card)
    if not saved:
        print("❌ Image creation failed."); sys.exit(1)

    # Facebook caption = Taglish reaction + full story (richer than the image)
    fb_msg = f"{result['caption']}\n\n{result['post']}" if result["caption"] else result["post"]

    if dry_run:
        print("\n[DRY RUN ✓] Skipping Facebook post.")
        print(f"  Message preview: {fb_msg[:150]}...")
        print(f"  Image: {saved}")
        return

    print("\n[3/4] Posting to Facebook...")
    ok = lp_post_image(saved, fb_msg, first_comment="Follow us: @lawrenceprecioussia")
    print("\n✅ Done!" if ok else "\n❌ Post failed.")


def run_poll_post(dry_run: bool):
    print("\n[1/2] Generating poll post...")
    result = generate_poll_post()
    print(f"\n  QUESTION: {result['question']}")
    for opt in result["options"]:
        print(f"  {opt}")

    if dry_run:
        print("\n[DRY RUN ✓] Skipping Facebook post.")
        print(f"\nFull message:\n{result['fb_message']}")
        return

    print("\n[2/2] Posting to Facebook...")
    ok = lp_post_text(result["fb_message"])
    print("\n✅ Done!" if ok else "\n❌ Post failed.")


def run_news_post(dry_run: bool):
    print("\n[1/5] Fetching LP news articles...")
    articles = fetch_top_articles(max_articles=5)
    if not articles:
        print("  ⚠️ No relevant articles found today. Skipping news post.")
        print("  (This is normal — the filter rejected all articles as off-topic.)")
        print("  The daily text post will still run at 8 PM SGT as scheduled.")
        sys.exit(0)  # Exit cleanly — not a failure, just nothing to post

    best = articles[0]
    print(f"  Selected: {best['title'][:70]}")
    print(f"  Source:   {best['source']} | Score: {best['score']}")

    print("\n[2/5] Generating news hook...")
    result = generate_news_hook(best)
    print(f"\n  POST:    {result['post']}")
    print(f"  CAPTION: {result['caption']}")

    print("\n[3/5] Generating image...")
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    img_path = str(OUTPUT_DIR / f"lp_news_{ts}.jpg")
    saved = create_post_image(post_text=result["post"], output_path=img_path, tone="serious")
    if not saved:
        print("❌ Image generation failed."); sys.exit(1)

    fb_msg = f"{result['caption']}\n\n{result['post']}" if result["caption"] else result["post"]
    # Let readers know the full article link is in the first comment
    if result.get("article_url"):
        fb_msg += "\n\n🔗 Full article in the first comment below."

    if dry_run:
        print("\n[DRY RUN ✓] Skipping Facebook post.")
        print(f"  Message preview: {fb_msg[:150]}...")
        print(f"  Image: {saved}")
        print(f"  Link:  {result['article_url']}")
        return

    print("\n[4/5] Posting to Facebook...")
    first_comment = f"🔗 Read more: {result['article_url']}" if result["article_url"] else ""
    ok = lp_post_image(saved, fb_msg, first_comment=first_comment)

    if ok:
        print("\n[5/5] Saving article to LP history...")
        save_posted_article(best)
        print("✅ Done!")
    else:
        print("\n❌ Post failed.")


def run_cta_post(dry_run: bool):
    # Bi-weekly gate — skip on odd ISO weeks
    week = datetime.date.today().isocalendar()[1]
    if not dry_run and week % 2 != 0:
        print(f"  Odd week ({week}) — skipping CTA post this Sunday.")
        return

    print("\n[1/2] Loading CTA post...")
    result = get_cta_post()
    fb_msg = f"{result['caption']}\n\n{result['post']}"
    print(f"  CAPTION: {result['caption']}")
    print(f"  POST preview: {result['post'][:120]}...")

    if dry_run:
        print("\n[DRY RUN ✓] Skipping Facebook post.")
        print(f"\nFull message:\n{fb_msg}")
        return

    print("\n[2/2] Posting to Facebook...")
    ok = lp_post_text(fb_msg)
    print("\n✅ Done!" if ok else "\n❌ Post failed.")


def run_faith_post(dry_run: bool):
    print("\n[1/3] Generating Sunday faith post...")
    result = generate_faith_post()
    print(f"\n  CATEGORY: {result.get('category', 'N/A')}")
    print(f"  VERSE:    {result.get('verse', 'N/A')}")
    print(f"  CAPTION:  {result['caption']}")
    print(f"  VERSE TEXT (image):\n  {result['verse_text'][:120]}...")
    print(f"  POST (caption):\n  {result['post'][:120]}...")

    # Image card shows ONLY the Bible verse — clean, no reflection text
    print("\n[2/3] Creating text card...")
    ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    img_path = str(OUTPUT_DIR / f"lp_faith_{ts}.jpg")
    saved    = create_text_card(post_text=result["verse_text"], output_path=img_path)
    if not saved:
        print("  Warning: Text card failed. Posting as text only.")

    # Facebook caption = Taglish reaction + reflection + lesson
    fb_msg = f"{result['caption']}\n\n{result['post']}"

    if dry_run:
        print("\n[DRY RUN] Skipping Facebook post.")
        print(f"\nImage text (verse only):\n{result['verse_text']}")
        print(f"\nFull FB message:\n{fb_msg}")
        return

    print("\n[3/3] Posting to Facebook...")
    if saved:
        ok = lp_post_image(saved, fb_msg)
    else:
        ok = lp_post_text(fb_msg)
    print("\nDone!" if ok else "\nPost failed.")
    # Bi-weekly gate — skip on odd ISO weeks
    week = datetime.date.today().isocalendar()[1]
    if not dry_run and week % 2 != 0:
        print(f"  Odd week ({week}) — skipping CTA post this Sunday.")
        return

    print("\n[1/2] Loading CTA post...")
    result = get_cta_post()
    fb_msg = f"{result['caption']}\n\n{result['post']}"
    print(f"  CAPTION: {result['caption']}")
    print(f"  POST preview: {result['post'][:100]}...")

    if dry_run:
        print("\n[DRY RUN ✓] Skipping Facebook post.")
        print(f"\nFull message:\n{fb_msg}")
        return

    print("\n[2/2] Posting to Facebook...")
    ok = lp_post_text(fb_msg)
    print("\n✅ Done!" if ok else "\n❌ Post failed.")


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 60)
    print(f"  🌟 @lawrenceprecioussia | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    parser = argparse.ArgumentParser(description="@lawrenceprecioussia Facebook Automation")
    parser.add_argument("--type",    default="text", choices=["text", "poll", "news", "cta", "faith"],
                        help="Post type")
    parser.add_argument("--format",  default=os.environ.get("POST_FORMAT", "any"),
                        help="Format: A / B / BW / C / D / E / any")
    parser.add_argument("--hook",    default=os.environ.get("POST_HOOK", "any"),
                        help="Hook: HUMOR / PAIN / DREAM / WISDOM / PRIDE / any")
    parser.add_argument("--dry-run", action="store_true",
                        help="Generate without posting to Facebook")
    args = parser.parse_args()

    print(f"  Type: {args.type} | Format: {args.format} | Hook: {args.hook} | Dry-run: {args.dry_run}\n")

    if args.type == "text":
        run_text_post(args.format, args.hook, args.dry_run)
    elif args.type == "poll":
        run_poll_post(args.dry_run)
    elif args.type == "news":
        run_news_post(args.dry_run)
    elif args.type == "cta":
        run_cta_post(args.dry_run)
    elif args.type == "faith":
        run_faith_post(args.dry_run)


if __name__ == "__main__":
    main()
