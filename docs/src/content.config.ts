import { defineCollection, z } from 'astro:content';
import { docsLoader } from '@astrojs/starlight/loaders';
import { docsSchema } from '@astrojs/starlight/schema';

export const collections = {
	docs: defineCollection({
		loader: docsLoader(),
		schema: docsSchema({
			// Blog posts carry a dateline, a category, and authors for the article header.
			extend: z.object({
				date: z.string().optional(),
				category: z.string().optional(),
				authors: z.string().optional(),
				cover: z.enum(['teal', 'violet', 'amber']).optional(),
			}),
		}),
	}),
};
