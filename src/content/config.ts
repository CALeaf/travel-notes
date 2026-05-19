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
      // Approximate coordinates for the trip's central location, used by /map/.
      // [lat, lng] in decimal degrees.
      coords: z.tuple([z.number(), z.number()]).optional(),
      draft: z.boolean().default(false),
    }),
});

export const collections = { posts };
