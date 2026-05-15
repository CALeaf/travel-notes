import { defineCollection, z } from 'astro:content';

const posts = defineCollection({
  type: 'content',
  schema: ({ image }) =>
    z.object({
      title: z.string(),
      date: z.coerce.date(),
      country: z.string(),
      city: z.string(),
      tags: z.array(z.string()).default([]),
      excerpt: z.string().max(220),
      cover: image(),
      gallery: z.array(image()).optional(),
      draft: z.boolean().default(false),
    }),
});

export const collections = { posts };
