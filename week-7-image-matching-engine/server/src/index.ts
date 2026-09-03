import express from "express";
import cors from "cors";
import { config } from "./config.js";
import imageRoutes from "./routes/images.js";
import postRoutes from "./routes/posts.js";
import reviewRoutes from "./routes/reviews.js";

const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Health check
app.get("/health", (_req, res) => {
  res.json({ status: "ok", timestamp: new Date().toISOString() });
});

// Routes
app.use("/images", imageRoutes);
app.use("/posts", postRoutes);
app.use("/suggestions", reviewRoutes);

// 404 handler
app.use((_req, res) => {
  res.status(404).json({ error: "Not found" });
});

// Global error handler
app.use((err: Error, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
  console.error("Unhandled error:", err);
  res.status(500).json({ error: "Internal server error" });
});

app.listen(config.port, () => {
  console.log(`🚀 Image Matching API running on http://localhost:${config.port}`);
  console.log(`   Health: http://localhost:${config.port}/health`);
});

export default app;
