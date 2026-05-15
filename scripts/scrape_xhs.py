"""
Xiaohongshu (小红书) scraper for the Field Notes site.

What it does:
1. Opens a real Chromium window via Playwright.
2. First run: stops at the login page and waits for you to scan the QR with the XHS app.
3. Once logged in, persists cookies to scripts/cookies.json so subsequent runs are non-interactive.
4. Visits the user profile URL, scrolls until all notes are loaded, then opens each note in turn.
5. Extracts title, body, date, tags, and image URLs.
6. Writes one Markdown file per note to src/content/_raw/<slug>.zh.md (Chinese original, with frontmatter).
7. Downloads original-resolution images to src/assets/notes/<slug>/.

Usage:
    cd /Users/bytedance/Downloads/travel-notes
    python3 -m venv .venv && source .venv/bin/activate
    pip install playwright beautifulsoup4 requests python-slugify
    python -m playwright install chromium

    # First run — show the browser, scan QR, scrape:
    PROFILE_URL="https://www.xiaohongshu.com/user/profile/<your_user_id>" \
        python scripts/scrape_xhs.py

    # Resume run (skip already-scraped notes):
    python scripts/scrape_xhs.py

Notes:
- XHS rate-limits aggressively. Default delay is 6–12 seconds per note. Do not lower it.
- Some selectors change over time — if scraping breaks, inspect the page in DevTools and patch
  the SELECTORS dict near the top of this file.
- Video notes are skipped (no public video download endpoint).
"""

from __future__ import annotations

import json
import os
import random
import re
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

try:
    from playwright.sync_api import sync_playwright, Page, BrowserContext
except ImportError:
    sys.exit("playwright not installed. Run: pip install playwright && python -m playwright install chromium")

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("beautifulsoup4 not installed. Run: pip install beautifulsoup4")

try:
    import requests
except ImportError:
    sys.exit("requests not installed. Run: pip install requests")

try:
    from slugify import slugify
except ImportError:
    # Fallback: simple ASCII-only slugifier
    def slugify(text: str, max_length: int = 60) -> str:
        s = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip().lower()
        s = re.sub(r"[\s_]+", "-", s)
        return s[:max_length] or "untitled"


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "src" / "content" / "_raw"
ASSETS_DIR = ROOT / "src" / "assets" / "notes"
COOKIES_PATH = Path(__file__).parent / "cookies.json"
PROGRESS_PATH = Path(__file__).parent / ".scrape_progress.json"

PROFILE_URL = os.environ.get("PROFILE_URL", "").strip()

# These selectors are XHS' current DOM. They will drift. If you see "no notes
# found", open the page in a browser and update them.
SELECTORS = {
    "note_card_link": "a.cover, a[href^='/explore/']",
    "title": "#detail-title, .note-content .title, h1",
    "body": "#detail-desc, .note-content .desc, .desc",
    "date": ".date, time",
    "tag": ".tag, a.tag",
    "image": ".swiper-slide img, .note-content img, .media-container img",
}

# Throttling
MIN_DELAY = 6.0
MAX_DELAY = 12.0


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

@dataclass
class Note:
    note_id: str
    url: str
    title: str
    body: str
    date_iso: str  # YYYY-MM-DD
    tags: list[str]
    image_urls: list[str]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_progress() -> set[str]:
    if PROGRESS_PATH.exists():
        return set(json.loads(PROGRESS_PATH.read_text()))
    return set()


def save_progress(done: set[str]) -> None:
    PROGRESS_PATH.write_text(json.dumps(sorted(done), ensure_ascii=False, indent=2))


def jitter() -> None:
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))


def upgrade_image_url(url: str) -> str:
    """Strip XHS thumbnail params to request the original-resolution image."""
    if "?" in url:
        url = url.split("?", 1)[0]
    # Some URLs encode size in the path: /thumbnail_xxx_!360x360.jpg
    url = re.sub(r"!\d+x\d+\.(jpg|png|webp|jpeg)$", r".\1", url, flags=re.I)
    return url


def make_slug(note_id: str, title: str) -> str:
    base = slugify(title, max_length=50) if title else ""
    if not base:
        return note_id
    # Append last 6 chars of note_id to ensure uniqueness if titles collide
    return f"{base}-{note_id[-6:]}" if len(note_id) >= 6 else f"{base}-{note_id}"


def write_markdown(note: Note, slug: str, image_filenames: list[str]) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    cover = image_filenames[0] if image_filenames else ""
    fm_lines = [
        "---",
        f'title: "{note.title.replace(chr(34), chr(39))}"',
        f"date: {note.date_iso}",
        "country: \"\"   # TODO fill or let rewrite step infer",
        "city: \"\"      # TODO fill or let rewrite step infer",
        f"tags: {json.dumps(note.tags, ensure_ascii=False)}",
        f'cover: ../../assets/notes/{slug}/{cover}' if cover else "cover: \"\"",
        f"source_url: {note.url}",
        "---",
        "",
        note.body.strip(),
        "",
    ]
    if image_filenames:
        fm_lines.append("\n## 原文配图\n")
        for fn in image_filenames:
            fm_lines.append(f"![](../../assets/notes/{slug}/{fn})")
            fm_lines.append("")
    out_path = RAW_DIR / f"{slug}.zh.md"
    out_path.write_text("\n".join(fm_lines), encoding="utf-8")
    return out_path


def download_images(urls: list[str], slug: str) -> list[str]:
    target = ASSETS_DIR / slug
    target.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    sess = requests.Session()
    sess.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
            "Referer": "https://www.xiaohongshu.com/",
        }
    )
    for i, url in enumerate(urls, start=1):
        url = upgrade_image_url(url)
        ext = Path(urlparse(url).path).suffix or ".jpg"
        if ext.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            ext = ".jpg"
        fname = f"cover{ext}" if i == 1 else f"{i:02d}{ext}"
        out = target / fname
        if out.exists() and out.stat().st_size > 0:
            saved.append(fname)
            continue
        try:
            r = sess.get(url, timeout=20)
            r.raise_for_status()
            out.write_bytes(r.content)
            saved.append(fname)
        except Exception as e:
            print(f"  ! failed to download {url}: {e}")
    return saved


# ---------------------------------------------------------------------------
# Playwright flows
# ---------------------------------------------------------------------------

def is_logged_in(page: Page, profile_url: str) -> bool:
    """The only reliable signal is page behavior: navigate to a profile URL and
    see if XHS redirects you to /login. Cookie names drift; this doesn't."""
    try:
        page.goto(profile_url, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
        return "/login" not in page.url
    except Exception:
        return False


def login_if_needed(context: BrowserContext, page: Page, profile_url: str) -> None:
    if is_logged_in(page, profile_url):
        print(">> Already logged in.", flush=True)
        COOKIES_PATH.write_text(
            json.dumps(context.storage_state(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return

    print(">> Login required. The Chromium window shows a QR code.", flush=True)
    print(">> 1) Open the Xiaohongshu app on your phone -> tap the scan icon (top-right of '我' tab)", flush=True)
    print(">> 2) Scan the QR code in the Chromium window", flush=True)
    print(">> 3) Tap '确认登录' on your phone to confirm", flush=True)
    print(">> Polling page state every 5s for up to 5 minutes...", flush=True)

    for i in range(60):
        page.wait_for_timeout(5000)
        if is_logged_in(page, profile_url):
            print(f">> Login detected (after ~{(i+1)*5}s).", flush=True)
            COOKIES_PATH.write_text(
                json.dumps(context.storage_state(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return
        if (i + 1) % 6 == 0:
            print(f"   ...still waiting ({(i+1)*5}s elapsed). Did you tap '确认登录' on your phone?", flush=True)

    raise SystemExit(
        "Login timed out after 5 minutes. Make sure you tapped '确认登录' on your phone "
        "after scanning. Re-run the script to try again."
    )


def collect_note_urls(page: Page, profile_url: str) -> list[str]:
    """Collect note URLs by scrolling. Uses a wide net of href patterns since
    XHS' DOM class names obfuscate often."""
    page.goto(profile_url, wait_until="domcontentloaded")
    page.wait_for_timeout(3500)

    href_patterns = re.compile(
        r"(?:^|/)(explore|discovery/item|user/profile/[^/]+/note)/[a-f0-9]{20,}"
        r"|^/explore/[a-zA-Z0-9]+"
        r"|/discovery/item/[a-zA-Z0-9]+"
    )
    seen: set[str] = set()
    stagnant_rounds = 0

    while stagnant_rounds < 5:
        # Pull every <a href> on the page via a single JS eval — faster than locator iteration
        hrefs = page.evaluate(
            "Array.from(document.querySelectorAll('a[href]')).map(a => a.getAttribute('href'))"
        )
        before = len(seen)
        for href in hrefs:
            if not href:
                continue
            if "/explore/" in href or "/discovery/item/" in href:
                full = href if href.startswith("http") else f"https://www.xiaohongshu.com{href}"
                seen.add(full.split("?", 1)[0])
        if len(seen) == before:
            stagnant_rounds += 1
        else:
            stagnant_rounds = 0
        page.mouse.wheel(0, 3500)
        page.wait_for_timeout(1800)

    if not seen:
        # Fallback: dump page state to /tmp so we can debug selectors
        debug_html = Path("/tmp/xhs_profile_empty.html")
        debug_png = Path("/tmp/xhs_profile_empty.png")
        debug_html.write_text(page.content(), encoding="utf-8")
        try:
            page.screenshot(path=str(debug_png), full_page=True)
        except Exception:
            pass
        sample = page.evaluate(
            "Array.from(document.querySelectorAll('a[href]')).slice(0, 50).map(a => a.getAttribute('href'))"
        )
        print("!! collect_note_urls found 0 candidates.", flush=True)
        print(f"!! Dumped page HTML -> {debug_html} and screenshot -> {debug_png}", flush=True)
        print("!! Sample of first 50 anchor hrefs on the page:", flush=True)
        for h in sample:
            print(f"     {h}", flush=True)

    return sorted(seen)


def parse_note(page: Page, url: str) -> Note | None:
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(2500)
    html = page.content()
    soup = BeautifulSoup(html, "html.parser")

    # Skip video notes
    if soup.find("video"):
        print("  - video note, skipping")
        return None

    note_id = url.rstrip("/").split("/")[-1]

    title_el = soup.select_one(SELECTORS["title"])
    title = title_el.get_text(strip=True) if title_el else ""
    if not title:
        # Fall back to first line of body
        body_el = soup.select_one(SELECTORS["body"])
        if body_el:
            title = body_el.get_text("\n", strip=True).split("\n", 1)[0][:60]

    body_el = soup.select_one(SELECTORS["body"])
    body = body_el.get_text("\n", strip=True) if body_el else ""

    date_el = soup.select_one(SELECTORS["date"])
    raw_date = date_el.get_text(strip=True) if date_el else ""
    # Best-effort date parse: looks like "2024-04-12" or "04-12" or "今天 12:30"
    m = re.search(r"(20\d{2})-(\d{1,2})-(\d{1,2})", raw_date)
    if m:
        date_iso = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    else:
        m2 = re.search(r"(\d{1,2})-(\d{1,2})", raw_date)
        year = time.localtime().tm_year
        if m2:
            date_iso = f"{year}-{int(m2.group(1)):02d}-{int(m2.group(2)):02d}"
        else:
            date_iso = time.strftime("%Y-%m-%d")

    tags = [t.get_text(strip=True).lstrip("#") for t in soup.select(SELECTORS["tag"])]
    tags = [t for t in tags if t]

    image_urls: list[str] = []
    for img in soup.select(SELECTORS["image"]):
        src = img.get("src") or img.get("data-src")
        if src and src.startswith("http") and src not in image_urls:
            image_urls.append(src)

    return Note(
        note_id=note_id,
        url=url,
        title=title or "Untitled",
        body=body,
        date_iso=date_iso,
        tags=tags,
        image_urls=image_urls,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # Force line-buffered stdout so monitor + tee see progress in real time.
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

    if not PROFILE_URL:
        sys.exit(
            "Set PROFILE_URL to your XHS profile URL, e.g.\n"
            "  PROFILE_URL='https://www.xiaohongshu.com/user/profile/<id>' "
            "python scripts/scrape_xhs.py"
        )

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    done = load_progress()

    headless_env = os.environ.get("HEADLESS", "").lower()
    # Default heuristic: if cookies already exist, run headless (more stable —
    # nothing to accidentally close). If no cookies, run headed so the user can
    # scan the QR.
    headless = headless_env in {"1", "true", "yes"} or (
        headless_env not in {"0", "false", "no"} and COOKIES_PATH.exists()
    )

    with sync_playwright() as p:
        storage_state = str(COOKIES_PATH) if COOKIES_PATH.exists() else None
        print(f">> Launching Chromium (headless={headless}).", flush=True)
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            storage_state=storage_state,
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
            ),
            locale="zh-CN",
        )
        page = context.new_page()

        login_if_needed(context, page, PROFILE_URL)
        # Persist any new cookies after login
        try:
            COOKIES_PATH.write_text(
                json.dumps(context.storage_state(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

        print(f">> Collecting note URLs from {PROFILE_URL}", flush=True)
        urls = collect_note_urls(page, PROFILE_URL)
        print(f">> Found {len(urls)} notes ({len(done)} already done).")

        for idx, url in enumerate(urls, start=1):
            if url in done:
                continue
            print(f"[{idx}/{len(urls)}] {url}")
            try:
                note = parse_note(page, url)
            except Exception as e:
                print(f"  ! parse failed: {e}")
                continue
            if not note:
                done.add(url)
                save_progress(done)
                jitter()
                continue
            slug = make_slug(note.note_id, note.title)
            print(f"  title: {note.title!r}")
            print(f"  date: {note.date_iso}, images: {len(note.image_urls)}, tags: {note.tags}")
            saved_imgs = download_images(note.image_urls, slug)
            md_path = write_markdown(note, slug, saved_imgs)
            print(f"  -> {md_path.relative_to(ROOT)}")
            done.add(url)
            save_progress(done)
            jitter()

        browser.close()
    print(">> Done.")


if __name__ == "__main__":
    main()
