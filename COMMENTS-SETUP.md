# Enabling comments (Giscus)

Comments are powered by **[Giscus](https://giscus.app)**, which uses GitHub
Discussions as the comment store. Free, no tracking, no third-party database.

Until you finish the setup below, post pages show a small "comments not yet
wired up" placeholder instead of the comment widget.

## One-time setup

1. **Enable Discussions on the repo**
   - GitHub repo → **Settings** → **General** → scroll to **Features** → check
     **Discussions**.

2. **Install the giscus GitHub App on this repo**
   - Visit https://github.com/apps/giscus
   - Click **Install** → choose **Only select repositories** → pick
     `travel-notes`.

3. **Get the config from giscus.app**
   - Visit https://giscus.app
   - Repository: `CALeaf/travel-notes`
   - Page ↔ Discussions Mapping: **pathname** (already set in code)
   - Discussion Category: **General** (or create one called `Comments`)
   - It will generate a `<script>` tag. From that snippet, copy the values of:
     - `data-repo-id`
     - `data-category-id`

4. **Paste them into `src/components/Comments.astro`**
   ```ts
   const GISCUS_REPO_ID = 'R_kgDOXXXXXXXX';        // paste here
   const GISCUS_CATEGORY_ID = 'DIC_kwDOXXXXXXXX';  // paste here
   ```
   Commit + push. The comment widget will show up on every post page.

That's it. Each post page's URL becomes a Discussion thread automatically.
Readers sign in with GitHub to comment.
