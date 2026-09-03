import { Router, Request, Response } from "express";
import prisma from "../db.js";
import { SuggestionQuerySchema, ReviewActionSchema } from "../schemas/suggestion.js";

const router = Router();

/**
 * GET /suggestions
 * List suggestions with optional filtering by status or postId.
 */
router.get("/", async (req: Request, res: Response) => {
  try {
    const query = SuggestionQuerySchema.safeParse(req.query);
    if (!query.success) {
      res.status(400).json({ error: "Invalid query parameters", details: query.error.flatten() });
      return;
    }

    const { status, postId, page, limit } = query.data;
    const skip = (page - 1) * limit;

    const where: Record<string, unknown> = {};
    if (status) where.status = status;
    if (postId) {
      if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(postId)) {
        const post = await prisma.post.findUnique({ where: { slug: postId } });
        where.postId = post?.id ?? postId;
      } else {
        where.postId = postId;
      }
    }

    const [suggestions, total] = await Promise.all([
      prisma.suggestion.findMany({
        where,
        skip,
        take: limit,
        orderBy: { createdAt: "desc" },
        include: {
          image: {
            select: {
              id: true,
              filename: true,
              subject: true,
              category: true,
              caption: true,
            },
          },
          post: {
            select: {
              id: true,
              title: true,
              slug: true,
            },
          },
        },
      }),
      prisma.suggestion.count({ where }),
    ]);

    res.json({
      data: suggestions,
      pagination: { page, limit, total, totalPages: Math.ceil(total / limit) },
    });
  } catch (error) {
    console.error("Error fetching suggestions:", error);
    res.status(500).json({ error: "Internal server error" });
  }
});

/**
 * GET /suggestions/:id
 * Get a single suggestion by ID.
 */
router.get("/:id", async (req: Request, res: Response) => {
  try {
    const suggestion = await prisma.suggestion.findUnique({
      where: { id: req.params.id },
      include: {
        image: true,
        post: true,
      },
    });

    if (!suggestion) {
      res.status(404).json({ error: "Suggestion not found" });
      return;
    }

    res.json({ data: suggestion });
  } catch (error) {
    console.error("Error fetching suggestion:", error);
    res.status(500).json({ error: "Internal server error" });
  }
});

/**
 * POST /suggestions/:id/approve
 * Approve a suggestion.
 */
router.post("/:id/approve", async (req: Request, res: Response) => {
  try {
    const parsed = ReviewActionSchema.safeParse(req.body ?? {});
    if (!parsed.success) {
      res.status(400).json({ error: "Validation failed", details: parsed.error.flatten() });
      return;
    }

    const suggestion = await prisma.suggestion.findUnique({
      where: { id: req.params.id },
    });

    if (!suggestion) {
      res.status(404).json({ error: "Suggestion not found" });
      return;
    }

    const updated = await prisma.suggestion.update({
      where: { id: req.params.id },
      data: {
        status: "approved",
        reviewNote: parsed.data.reviewNote,
      },
      include: { image: true, post: true },
    });

    res.json({ data: updated });
  } catch (error) {
    console.error("Error approving suggestion:", error);
    res.status(500).json({ error: "Internal server error" });
  }
});

/**
 * POST /suggestions/:id/reject
 * Reject a suggestion.
 */
router.post("/:id/reject", async (req: Request, res: Response) => {
  try {
    const parsed = ReviewActionSchema.safeParse(req.body ?? {});
    if (!parsed.success) {
      res.status(400).json({ error: "Validation failed", details: parsed.error.flatten() });
      return;
    }

    const suggestion = await prisma.suggestion.findUnique({
      where: { id: req.params.id },
    });

    if (!suggestion) {
      res.status(404).json({ error: "Suggestion not found" });
      return;
    }

    const updated = await prisma.suggestion.update({
      where: { id: req.params.id },
      data: {
        status: "rejected",
        reviewNote: parsed.data.reviewNote,
      },
      include: { image: true, post: true },
    });

    res.json({ data: updated });
  } catch (error) {
    console.error("Error rejecting suggestion:", error);
    res.status(500).json({ error: "Internal server error" });
  }
});

export default router;
