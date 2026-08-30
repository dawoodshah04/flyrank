import { Router, Request, Response } from "express";
import prisma from "../db";
import { CreatePostSchema, PostQuerySchema } from "../schemas/post";

const router = Router();

/**
 * GET /posts
 * List all posts with pagination.
 */
router.get("/", async (req: Request, res: Response) => {
  try {
    const query = PostQuerySchema.safeParse(req.query);
    if (!query.success) {
      res.status(400).json({ error: "Invalid query parameters", details: query.error.flatten() });
      return;
    }

    const { page, limit } = query.data;
    const skip = (page - 1) * limit;

    const [posts, total] = await Promise.all([
      prisma.post.findMany({
        skip,
        take: limit,
        orderBy: { createdAt: "desc" },
        select: {
          id: true,
          title: true,
          slug: true,
          content: true,
          tags: true,
          createdAt: true,
        },
      }),
      prisma.post.count(),
    ]);

    res.json({
      data: posts,
      pagination: { page, limit, total, totalPages: Math.ceil(total / limit) },
    });
  } catch (error) {
    console.error("Error fetching posts:", error);
    res.status(500).json({ error: "Internal server error" });
  }
});

/**
 * GET /posts/:id
 * Get a single post by ID or slug.
 */
router.get("/:id", async (req: Request, res: Response) => {
  try {
    const identifier = req.params.id;

    // Try UUID first, then slug
    const post = await prisma.post.findFirst({
      where: {
        OR: [
          { id: identifier },
          { slug: identifier },
        ],
      },
      select: {
        id: true,
        title: true,
        slug: true,
        content: true,
        tags: true,
        createdAt: true,
        updatedAt: true,
      },
    });

    if (!post) {
      res.status(404).json({ error: "Post not found" });
      return;
    }

    res.json({ data: post });
  } catch (error) {
    console.error("Error fetching post:", error);
    res.status(500).json({ error: "Internal server error" });
  }
});

/**
 * POST /posts
 * Create a new blog post.
 */
router.post("/", async (req: Request, res: Response) => {
  try {
    const parsed = CreatePostSchema.safeParse(req.body);
    if (!parsed.success) {
      res.status(400).json({ error: "Validation failed", details: parsed.error.flatten() });
      return;
    }

    const existing = await prisma.post.findUnique({ where: { slug: parsed.data.slug } });
    if (existing) {
      res.status(409).json({ error: `Post with slug '${parsed.data.slug}' already exists` });
      return;
    }

    const post = await prisma.post.create({
      data: parsed.data,
      select: {
        id: true,
        title: true,
        slug: true,
        content: true,
        tags: true,
        createdAt: true,
      },
    });

    res.status(201).json({ data: post });
  } catch (error) {
    console.error("Error creating post:", error);
    res.status(500).json({ error: "Internal server error" });
  }
});

/**
 * GET /posts/:id/images
 * Get ranked image suggestions for a post.
 * Python writes suggestions to the DB; this endpoint reads them.
 */
router.get("/:id/images", async (req: Request, res: Response) => {
  try {
    const identifier = req.params.id;

    // Resolve post by ID or slug
    const post = await prisma.post.findFirst({
      where: {
        OR: [
          { id: identifier },
          { slug: identifier },
        ],
      },
    });

    if (!post) {
      res.status(404).json({ error: "Post not found" });
      return;
    }

    const suggestions = await prisma.suggestion.findMany({
      where: { postId: post.id },
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
      },
      orderBy: { rank: "asc" },
    });

    // Separate passed and rejected
    const passed = suggestions.filter((s) => s.guardPassed);
    const rejected = suggestions.filter((s) => !s.guardPassed);

    // If no suggestion passed the guard
    if (passed.length === 0) {
      const bestRejected = rejected[0];
      res.json({
        match: null,
        reason: bestRejected
          ? `No confident match. Best candidate rejected: ${bestRejected.guardReason}`
          : "No image candidates found for this post.",
        allCandidates: suggestions.map((s) => ({
          id: s.id,
          image: s.image,
          similarityScore: s.similarityScore,
          guardPassed: s.guardPassed,
          guardReason: s.guardReason,
          rank: s.rank,
          status: s.status,
        })),
      });
      return;
    }

    res.json({
      match: {
        id: passed[0].id,
        image: passed[0].image,
        similarityScore: passed[0].similarityScore,
        guardReason: passed[0].guardReason,
        rank: passed[0].rank,
        status: passed[0].status,
      },
      allCandidates: suggestions.map((s) => ({
        id: s.id,
        image: s.image,
        similarityScore: s.similarityScore,
        guardPassed: s.guardPassed,
        guardReason: s.guardReason,
        rank: s.rank,
        status: s.status,
      })),
    });
  } catch (error) {
    console.error("Error fetching post images:", error);
    res.status(500).json({ error: "Internal server error" });
  }
});

export default router;
