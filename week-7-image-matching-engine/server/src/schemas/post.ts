import { z } from "zod";

// Request schemas for post endpoints

export const CreatePostSchema = z.object({
  title: z.string().min(1).max(500),
  slug: z.string().min(1).max(200).regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/, "Slug must be lowercase with hyphens"),
  content: z.string().min(10),
  tags: z.array(z.string()).default([]),
});

export type CreatePostInput = z.infer<typeof CreatePostSchema>;

export const PostQuerySchema = z.object({
  page: z.coerce.number().int().positive().default(1),
  limit: z.coerce.number().int().positive().max(100).default(20),
});

// The shape of a suggestion returned inside GET /posts/:id/images
export const PostImageSuggestionSchema = z.object({
  id: z.string().uuid(),
  image: z.object({
    id: z.string().uuid(),
    filename: z.string(),
    subject: z.string().nullable(),
    category: z.string().nullable(),
    caption: z.string().nullable(),
    confidence: z.number().nullable(),
  }),
  similarityScore: z.number(),
  guardPassed: z.boolean(),
  guardReason: z.string().nullable(),
  rank: z.number(),
  status: z.string(),
});
