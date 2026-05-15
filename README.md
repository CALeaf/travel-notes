# Field Notes — your travel blog

A static, searchable, English-language travel blog generated from your Xiaohongshu (小红书) notes. Magazine layout, big covers, full-text search, deploys to GitHub Pages on every push.

```
┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Xiaohongshu  │ →  │ Chinese drafts   │ →  │ English posts    │ →  Astro site
│ (your acct)  │    │ src/content/_raw │    │ src/content/posts│    + Pagefind
└──────────────┘    └──────────────────┘    └──────────────────┘
   Playwright           claude -p              Astro build
   scraper              (subscription)         + GitHub Pages
```

---

## Quick start (the 60-second version)

If you just want to see the site locally:

```bash
cd /Users/bytedance/Downloads/travel-notes
npm install        # one-time, ~30 seconds
npm run dev        # opens http://localhost:4321
```

Three sample posts ship with the repo so you can verify the layout before scraping anything.

---

## Full pipeline (scrape → rewrite → publish)

### 1. Install Node and Python deps

You need Node 18+ and Python 3.9+. On this machine both are already installed.

```bash
cd /Users/bytedance/Downloads/travel-notes

# Node deps (Astro, Tailwind, Pagefind)
npm install

# Python deps for the scraper, in a venv
python3 -m venv .venv
source .venv/bin/activate
pip install playwright beautifulsoup4 requests python-slugify
python -m playwright install chromium
```

### 2. Find your Xiaohongshu profile URL

1. Open https://www.xiaohongshu.com on a desktop browser.
2. Log in with the QR code if needed.
3. Click your avatar → "我的主页" (My profile).
4. Copy the URL from the address bar. It looks like:
   `https://www.xiaohongshu.com/user/profile/5abc123def456789012345`

### 3. Scrape your notes

```bash
# from the travel-notes/ directory, in your venv:
PROFILE_URL="https://www.xiaohongshu.com/user/profile/<your_id>" \
    python scripts/scrape_xhs.py
```

What happens:

1. A Chromium window opens. It's not headless on purpose — XHS detects automation.
2. **Scan the QR code with your XHS app the first time.** Cookies are saved to
   `scripts/cookies.json` so subsequent runs skip the QR step.
3. The script scrolls your profile to load every note, then opens each one in turn.
4. For each note it writes a Chinese-language Markdown file to
   `src/content/_raw/<slug>.zh.md` and downloads images to
   `src/assets/notes/<slug>/`.
5. Progress is saved after every note. You can Ctrl-C and resume; finished notes are skipped.

**Throttling:** the script sleeps 6–12 seconds between notes. Don't lower this. XHS
will silently shadow-rate-limit your account if you scrape too fast, and you'll
end up with empty pages and no error.

**Selector drift:** if the script reports "found 0 notes" or all bodies are
empty, XHS changed their DOM. Open `scripts/scrape_xhs.py` and update the
`SELECTORS` dict (top of the file) to match what you see in DevTools.

### 4. Rewrite to English

This is where every note gets turned into a polished English blog post. The
script uses the local `claude` CLI, which goes through your Claude Code
subscription — **no API key, no Anthropic API charges.**

```bash
bash scripts/rewrite_to_english.sh
```

What happens:

1. For each `src/content/_raw/*.zh.md`, the script feeds the prompt at
   `scripts/prompts/rewrite_blog.md` plus the Chinese note to `claude -p`.
2. The output is written to `src/content/posts/<slug>.md`.
3. Existing files are skipped (idempotent). Use `--force` to re-process.

After it finishes, **read 3-5 random posts** before you trust the batch. If
the language sounds like Google Translate, edit `scripts/prompts/rewrite_blog.md`
to tighten the voice rules and re-run with `--force`.

```bash
# Re-process everything after editing the prompt:
bash scripts/rewrite_to_english.sh --force

# Or re-process a single file:
bash scripts/rewrite_to_english.sh src/content/_raw/some-slug.zh.md --force
```

### 5. Verify locally

```bash
npm run dev
```

Visit http://localhost:4321. You should see your posts grouped by country.
Search is disabled in dev (it's generated at build time). To test search:

```bash
npm run build
npm run preview
```

### 6. Replace covers with your own photos

Each post's images live in `src/assets/notes/<slug>/`. The scraper saves the
small Xiaohongshu-compressed versions as `cover.jpg`, `02.jpg`, `03.jpg`, etc.

To use your own high-res versions:

1. Drop your photo into the same directory, naming it `cover.jpg` to overwrite
   the existing cover, or with a new name like `06.jpg` if you want it as
   inline content.
2. If you renamed the cover, edit the post's frontmatter:
   `cover: ../../assets/notes/<slug>/your-new-name.jpg`.
3. Save. The dev server hot-reloads. Astro automatically resizes and converts
   to WebP/AVIF on build, so it's fine to drop in 4MB originals.

### 7. Publish to GitHub Pages

One-time setup:

1. Create a new GitHub repo: https://github.com/new
   - Name it whatever (e.g. `field-notes` or `travel-notes`).
   - Make it public.
2. In the repo's **Settings → Pages**, set:
   - **Source:** GitHub Actions
3. In **Settings → Secrets and variables → Actions → Variables**, add:
   - `SITE_URL` = the URL the site will live at, e.g.
     `https://<your-username>.github.io/field-notes/`
4. Push the code:
   ```bash
   cd /Users/bytedance/Downloads/travel-notes
   git init
   git add -A
   git commit -m "init: field notes scaffold"
   git remote add origin git@github.com:<your-username>/<repo>.git
   git branch -M main
   git push -u origin main
   ```
5. Watch the **Actions** tab. The first build takes ~2 minutes. Once it goes
   green, the site is live at the URL you set above.

For subsequent updates: just `git push`. The Action rebuilds and redeploys.

If you want a custom domain later (e.g. `fieldnotes.your-domain.com`):

1. Buy the domain (Namecheap / Cloudflare ≈ ¥80/year for `.com`).
2. Add a CNAME record pointing to `<your-username>.github.io`.
3. In GitHub repo Settings → Pages, enter the custom domain. GitHub provisions
   a free SSL cert automatically.
4. Update `SITE_URL` to `https://your-custom-domain/` and re-run the workflow.

---

## Project layout

```
travel-notes/
├── src/
│   ├── content/
│   │   ├── _raw/              # Chinese drafts (gitignored)
│   │   └── posts/             # English blog posts (committed)
│   ├── assets/notes/<slug>/   # per-post images
│   ├── layouts/BaseLayout.astro
│   ├── components/            # PostCard, DestinationGroup, SearchBox
│   ├── pages/
│   │   ├── index.astro        # home — by-country grid
│   │   ├── about.astro
│   │   ├── search.astro
│   │   ├── posts/[slug].astro
│   │   └── destinations/[country].astro
│   └── styles/global.css
├── scripts/
│   ├── scrape_xhs.py          # Playwright scraper
│   ├── rewrite_to_english.sh  # claude -p batch
│   └── prompts/rewrite_blog.md
├── .github/workflows/deploy.yml
├── astro.config.mjs
├── tailwind.config.mjs
└── package.json
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `npm install` hangs | corporate proxy in shell env | `unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY` and retry |
| Scraper opens browser then nothing happens | Not logged in | Scan the QR with your phone's XHS app; the script polls for cookies |
| Scraper says "found 0 notes" | XHS DOM changed | Update `SELECTORS` in `scripts/scrape_xhs.py` |
| Body text is empty for all notes | Same selector drift | Same fix |
| Rewrites read like translations | Prompt isn't strong enough | Edit `scripts/prompts/rewrite_blog.md`, then `--force` rerun |
| Search box says "Search index is generated at build time" in dev | Expected — Pagefind only runs at build | Run `npm run build && npm run preview` to test search |
| Image doesn't show on detail page | Frontmatter `cover:` path wrong | Path must be relative from the .md, e.g. `../../assets/notes/<slug>/cover.jpg` |
| GitHub Action fails on `npm ci` | Node lockfile out of sync | Delete `package-lock.json`, run `npm install` locally, commit the new lockfile |
| Site looks unstyled on Pages | `BASE` mismatch | Set `vars.SITE_URL` in repo Actions → Variables to match the actual published URL, e.g. `https://user.github.io/repo/` |

---

## Costs

- **Hosting:** GitHub Pages — free.
- **LLM rewrites:** zero — uses your Claude Code subscription via `claude -p`. No API key required.
- **Domain (optional):** ~¥80/year if you want `your-name.com` instead of the default `*.github.io`.

Total: **0 元** to start, **80 元/year** if you upgrade to a custom domain.
