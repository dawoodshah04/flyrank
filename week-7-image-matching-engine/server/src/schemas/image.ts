import { z } from "zod";

// Response schemas for image endpoints

export const ImageResponseSchema = z.object({
  id: z.string().uuid(),
  filename: z.string(),
  filepath: z.string(),
  status: z.enum(["pending", "tagged", "low_confidence", "failed"]),
  subject: z.string().nullable(),
  category: z.string().nullable(),
  attributes: z.array(z.string()),
  caption: z.string().nullable(),
  confidence: z.number().nullable(),
  createdAt: z.date(),
});

export type ImageResponse = z.infer<typeof ImageResponseSchema>;

// Query params
export const ImageQuerySchema = z.object({
  status: z.enum(["pending", "tagged", "low_confidence", "failed"]).optional(),
  category: z.string().optional(),
  page: z.coerce.number().int().positive().default(1),
  limit: z.coerce.number().int().positive().max(100).default(20),
});
