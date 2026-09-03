import { Router, Request, Response } from "express";
import prisma from "../db.js";
import { ImageQuerySchema } from "../schemas/image.js";

const router = Router();

/**
 * GET /images
 * List all images with optional filtering by status and category.
 */
router.get("/", async (req: Request, res: Response) => {
  try {
    const query = ImageQuerySchema.safeParse(req.query);
    if (!query.success) {
      res.status(400).json({ error: "Invalid query parameters", details: query.error.flatten() });
      return;
    }

    const { status, category, page, limit } = query.data;
    const skip = (page - 1) * limit;

    const where: Record<string, string> = {};
    if (status) where.status = status;
    if (category) where.category = category;

    const [images, total] = await Promise.all([
      prisma.image.findMany({
        where,
        skip,
        take: limit,
        orderBy: { createdAt: "desc" },
        select: {
          id: true,
          filename: true,
          filepath: true,
          status: true,
          subject: true,
          category: true,
          attributes: true,
          caption: true,
          confidence: true,
          createdAt: true,
        },
      }),
      prisma.image.count({ where }),
    ]);

    res.json({
      data: images,
      pagination: { page, limit, total, totalPages: Math.ceil(total / limit) },
    });
  } catch (error) {
    console.error("Error fetching images:", error);
    res.status(500).json({ error: "Internal server error" });
  }
});

/**
 * GET /images/:id
 * Get a single image by ID with full metadata.
 */
router.get("/:id", async (req: Request, res: Response) => {
  try {
    const image = await prisma.image.findUnique({
      where: { id: req.params.id },
      select: {
        id: true,
        filename: true,
        filepath: true,
        status: true,
        subject: true,
        category: true,
        attributes: true,
        caption: true,
        confidence: true,
        createdAt: true,
        updatedAt: true,
      },
    });

    if (!image) {
      res.status(404).json({ error: "Image not found" });
      return;
    }

    res.json({ data: image });
  } catch (error) {
    console.error("Error fetching image:", error);
    res.status(500).json({ error: "Internal server error" });
  }
});

export default router;
