import type { APIRoute } from 'astro';

const robots = (sitemapURL: URL) => `User-agent: *
Allow: /

Sitemap: ${sitemapURL.href}
`;

export const GET: APIRoute = ({ site }) => {
  // Astro guarantees `site` is set (defined in astro.config.mjs).
  const sitemapURL = new URL('sitemap-index.xml', site);
  return new Response(robots(sitemapURL), {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
};
