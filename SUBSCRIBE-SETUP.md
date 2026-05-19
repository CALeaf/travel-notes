# Email subscriptions (Buttondown, free tier + manual send)

Email subscriptions go through **[Buttondown](https://buttondown.com)** on the
free tier (up to 1,000 subscribers).

The free tier supports the form widget that lives on your post pages and
About page, but **does not** include auto-send from RSS. So the workflow is:

1. You push a new post → site redeploys (≈ 1 min).
2. You manually compose and send one email in Buttondown that points to the
   new post.

Each manual send is about 2 minutes. The template below makes it copy-paste.

---

## After-publish checklist

Run this after every push of a new post:

- [ ] Confirm the post is live at `https://leavesnotes.com/posts/<slug>/`
- [ ] Go to https://buttondown.com → **New email**
- [ ] Paste the template below into the Subject + Body fields
- [ ] Replace the four placeholders: `TITLE`, `EXCERPT`, `SLUG`, `COVER_PATH`
- [ ] Click **Preview** to spot-check
- [ ] Click **Send to subscribers** (or **Send to self first** if you want a test run)

---

## Email template (copy-paste)

**Subject:**
```
TITLE
```

**Body (Markdown):**
```markdown
Hi friend,

New travel note up on the site:

## TITLE

EXCERPT

[Read the full post →](https://leavesnotes.com/posts/SLUG/)

— Xuenan
```

**Where to find the placeholders:**

| Placeholder | Where it comes from |
|---|---|
| `TITLE` | The `title:` field in the post's frontmatter |
| `EXCERPT` | The `excerpt:` field in the post's frontmatter |
| `SLUG` | The filename without `.md` — e.g. `eastern-canada-fall-loop` |
| `COVER_PATH` | (Optional) drag the cover image into Buttondown's editor for an image preview |

---

## Tip: send to yourself first

Buttondown's editor has a **"Send test email"** button. Use it the first time
or two until you trust the template. Once you've sent 2–3 successfully, skip
the test and go straight to publish.

---

## Why not auto-send?

Buttondown's RSS-to-Email feature is paid ($9/month and up). For ≤ 1 post per
week, manual send is cheaper *and* gives you a final eyes-on review before
emails go out. If you later start publishing > 1 post per week, switching to
Mailchimp's free RSS Campaign (or paying Buttondown $9/mo) becomes worth it.
