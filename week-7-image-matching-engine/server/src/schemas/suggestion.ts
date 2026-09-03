import { z } from "zod";

// Review action schemas

export const ReviewActionSchema = z.object({
  reviewNote: z.string().max(1000).optional(),
}).default({});

export type ReviewActionInput = z.infer<typeof ReviewActionSchema>;

export const SuggestionQuerySchema = z.object({
  status: z.enum(["pending", "approved", "rejected"]).optional(),
  postId: z.string().optional(),
  page: z.coerce.number().int().positive().default(1),
  limit: z.coerce.number().int().positive().max(100).default(20),
});
