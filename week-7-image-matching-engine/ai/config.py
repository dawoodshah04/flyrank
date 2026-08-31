"""Configuration loaded from .env in project root."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (one level up from ai/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# ── API Keys ──
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ── Database ──
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/image_matching",
)

# ── Thresholds (tuned via eval) ──
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.65"))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))

# ── Paths ──
CORPUS_DIR = PROJECT_ROOT / "corpus"

# ── Cost tracking (Gemini Flash free tier rates — $0 but we track anyway) ──
COST_PER_1K_INPUT_TOKENS = 0.0  # Free tier
COST_PER_1K_OUTPUT_TOKENS = 0.0  # Free tier
