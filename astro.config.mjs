import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';


// https://astro.build/config
// SITE / BASE come from env so the GitHub Actions workflow can override them
// without code changes. For local dev they fall back to localhost root.
//
// Deployment URLs:
//   - GitHub Pages project page:   SITE=https://caleaf.github.io  BASE=/travel-notes
//   - Custom domain (future):      SITE=https://your-domain        BASE=/
const SITE = process.env.SITE || 'http://localhost:4321';
const BASE = process.env.BASE || '/';

export default defineConfig({
  site: SITE,
  base: BASE,
  trailingSlash: 'always',
  integrations: [tailwind({ applyBaseStyles: false }), mdx(), sitemap()],
  image: {
    service: { entrypoint: 'astro/assets/services/sharp' },
  },
  markdown: {
    shikiConfig: { theme: 'github-light', wrap: true },
  },
});
