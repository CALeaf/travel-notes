# Enabling email subscriptions (Buttondown)

Email subscriptions are powered by **[Buttondown](https://buttondown.com)** —
free for up to 1,000 subscribers, no tracking, your subscriber list lives there
(not in your repo).

Until you finish the setup below, the form on post pages and the About page
shows a small "email subscription not yet wired up" placeholder.

## One-time setup

1. **Sign up at https://buttondown.com**
   - Pick a plan: **Free** (up to 1,000 subscribers).
   - Pick a username. Your subscribe URL will be `buttondown.com/<username>`.
   - Recommended username: `leavesnotes` (matches the domain). If taken, pick
     anything you'll remember.

2. **Paste the username into `src/components/Subscribe.astro`**
   ```ts
   const BUTTONDOWN_USERNAME = 'leavesnotes';  // <-- here
   ```
   Commit + push. The form goes live on the next deploy.

3. **(Recommended) Turn on RSS-to-Email**
   - In Buttondown, go to **Settings → Integrations → RSS-to-Email**.
   - Point it at `https://leavesnotes.com/rss.xml`.
   - Choose "Send drafts" so you can review each email before it goes out
     (otherwise it auto-sends as soon as RSS updates).
   - Each new post you publish becomes a draft email; you click Send.

That's it. Subscribers get a clean text email with the post title, excerpt,
and a link back to the live page.

## What subscribers see

When someone enters their email and clicks Subscribe, a Buttondown popup
window confirms the subscription. They then get a confirmation email asking
them to click to verify (double opt-in, anti-spam). After that they're on the
list.

## Where the form appears on the site

- Bottom of every post page (above comments).
- About page (below the LinkedIn button).
- Footer keeps the RSS link separately (for readers who use RSS readers).
