import { Router, Request, Response } from "express";
import prisma from "../db.js";
import { CreatePostSchema, PostQuerySchema } from "../schemas/post.js";

const router = Router();
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/**
 * GET /posts
 * List all posts with optional pagination.
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
 * Get a single post by UUID or slug.
 */
router.get("/:id", async (req: Request, res: Response) => {
  try {
    const identifier = req.params.id;
    const post = await prisma.post.findFirst({
      // PostgreSQL rejects a non-UUID value when it is compared to the UUID
      // primary key, so only include the id branch for actual UUIDs.
      where: UUID_PATTERN.test(identifier) ? { id: identifier } : { slug: identifier },
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
 * Create a new post.
 */
router.post("/", async (req: Request, res: Response) => {
  try {
    const parsed = CreatePostSchema.safeParse(req.body);
    if (!parsed.success) {
      res.status(400).json({ error: "Validation failed", details: parsed.error.flatten() });
      return;
    }

    const { title, slug, content, tags } = parsed.data;

    const post = await prisma.post.create({
      data: { title, slug, content, tags },
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
  } catch (error: any) {
    if (error?.code === "P2002") {
      res.status(409).json({ error: "A post with this slug already exists" });
      return;
    }
    console.error("Error creating post:", error);
    res.status(500).json({ error: "Internal server error" });
  }
});

/**
 * GET /posts/:id/images
 * Get image suggestions for a post.
 */
router.get("/:id/images", async (req: Request, res: Response) => {
  try {
    const identifier = req.params.id;
    const post = await prisma.post.findFirst({
      where: UUID_PATTERN.test(identifier) ? { id: identifier } : { slug: identifier },
    });
    if (!post) {
      res.status(404).json({ error: "Post not found" });
      return;
    }

    const suggestions = await prisma.suggestion.findMany({
      where: { postId: post.id, guardPassed: true },
      orderBy: { rank: "asc" },
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
    });

    const data = suggestions.map((s) => ({
      id: s.id,
      image: s.image,
      similarityScore: s.similarityScore,
      guardPassed: s.guardPassed,
      guardReason: s.guardReason,
      rank: s.rank,
      status: s.status,
    }));

    res.json({
      data,
      match: data[0] ?? null,
      message: data.length === 0 ? "No confident match found" : undefined,
    });
  } catch (error) {
    console.error("Error fetching post images:", error);
    res.status(500).json({ error: "Internal server error" });
  }
});

export default router;
