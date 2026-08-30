import { Router, Request, Response } from "express";
import prisma from "../db";
import { ReviewActionSchema, SuggestionQuerySchema } from "../schemas/suggestion";

const router = Router();

/**
 * GET /suggestions
 * List suggestions with optional filtering by status and postId.
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

    const where: Record<string, string> = {};
    if (status) where.status = status;
    if (postId) where.postId = postId;

    const [suggestions, total] = await Promise.all([
      prisma.suggestion.findMany({
        where,
        skip,
        take: limit,
        include: {
          image: {
            select: {
              id: true,
              filename: true,
              subject: true,
              category: true,
              caption: true,
              confidence: true,
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
        orderBy: { createdAt: "desc" },
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
 * Inspect a single suggestion — why was this image suggested or rejected?
 */
router.get("/:id", async (req: Request, res: Response) => {
  try {
    const suggestion = await prisma.suggestion.findUnique({
      where: { id: req.params.id },
      include: {
        image: {
          select: {
            id: true,
            filename: true,
            subject: true,
            category: true,
            attributes: true,
            caption: true,
            confidence: true,
          },
        },
        post: {
          select: {
            id: true,
            title: true,
            slug: true,
            tags: true,
          },
        },
      },
    });

    if (!suggestion) {
      res.status(404).json({ error: "Suggestion not found" });
      return;
    }

    res.json({
      data: {
        ...suggestion,
        explanation: {
          similarityScore: suggestion.similarityScore,
          guardPassed: suggestion.guardPassed,
          guardReason: suggestion.guardReason,
          imageSubject: suggestion.image.subject,
          imageCategory: suggestion.image.category,
          imageConfidence: suggestion.image.confidence,
          postTags: suggestion.post.tags,
        },
      },
    });
  } catch (error) {
    console.error("Error fetching suggestion:", error);
    res.status(500).json({ error: "Internal server error" });
  }
});

/**
 * POST /suggestions/:id/approve
 * Approve a suggested image-post pairing.
 */
router.post("/:id/approve", async (req: Request, res: Response) => {
  try {
    const parsed = ReviewActionSchema.safeParse(req.body);
    if (!parsed.success) {
      res.status(400).json({ error: "Validation failed", details: parsed.error.flatten() });
      return;
    }

    const suggestion = await prisma.suggestion.findUnique({ where: { id: req.params.id } });
    if (!suggestion) {
      res.status(404).json({ error: "Suggestion not found" });
      return;
    }

    if (suggestion.status !== "pending") {
      res.status(409).json({ error: `Suggestion already ${suggestion.status}` });
      return;
    }

    const updated = await prisma.suggestion.update({
      where: { id: req.params.id },
      data: {
        status: "approved",
        reviewNote: parsed.data.reviewNote || null,
      },
    });

    res.json({ data: updated });
  } catch (error) {
    console.error("Error approving suggestion:", error);
    res.status(500).json({ error: "Internal server error" });
  }
});

/**
 * POST /suggestions/:id/reject
 * Reject a suggested image-post pairing with an optional note.
 */
router.post("/:id/reject", async (req: Request, res: Response) => {
  try {
    const parsed = ReviewActionSchema.safeParse(req.body);
    if (!parsed.success) {
      res.status(400).json({ error: "Validation failed", details: parsed.error.flatten() });
      return;
    }

    const suggestion = await prisma.suggestion.findUnique({ where: { id: req.params.id } });
    if (!suggestion) {
      res.status(404).json({ error: "Suggestion not found" });
      return;
    }

    if (suggestion.status !== "pending") {
      res.status(409).json({ error: `Suggestion already ${suggestion.status}` });
      return;
    }

    const updated = await prisma.suggestion.update({
      where: { id: req.params.id },
      data: {
        status: "rejected",
        reviewNote: parsed.data.reviewNote || null,
      },
    });

    res.json({ data: updated });
  } catch (error) {
    console.error("Error rejecting suggestion:", error);
    res.status(500).json({ error: "Internal server error" });
  }
});

export default router;
