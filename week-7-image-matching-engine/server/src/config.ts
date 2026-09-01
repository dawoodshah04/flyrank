import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load .env from project root (one level up from server/)
dotenv.config({ path: path.resolve(__dirname, "../../.env") });

export const config = {
  port: parseInt(process.env.PORT || "3000", 10),
  databaseUrl: process.env.DATABASE_URL || "postgresql://postgres:postgres@localhost:5432/image_matching",
  similarityThreshold: parseFloat(process.env.SIMILARITY_THRESHOLD || "0.65"),
  confidenceThreshold: parseFloat(process.env.CONFIDENCE_THRESHOLD || "0.7"),
};
