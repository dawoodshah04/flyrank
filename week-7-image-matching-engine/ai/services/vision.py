"""Vision service — analyse images using Google Gemini vision model."""

import json
import base64
from pathlib import Path

import google.generativeai as genai

from ai.config import GEMINI_API_KEY, CONFIDENCE_THRESHOLD
from ai.schemas.vision import ImageAnalysis

genai.configure(api_key=GEMINI_API_KEY)

VISION_MODEL = "gemini-2.0-flash"

SYSTEM_PROMPT = """Analyse the image and return JSON with exactly these keys:
- "subject": the primary subject of the image (e.g. "red fox", "gray wolf", "mountain landscape")
- "category": a broad one-word category (e.g. "fox", "wolf", "dog", "bear", "mountain", "ocean")
- "caption": a one-sentence description of the image
- "attributes": an array of 3-7 keyword attributes describing the image
- "confidence": your confidence in this analysis from 0.0 to 1.0

Return ONLY valid JSON, no markdown fences."""


def analyse_image(image_path: str | Path) -> ImageAnalysis:
    """Send an image to the Gemini vision model and return structured analysis."""
    img_path = Path(image_path)
    raw = img_path.read_bytes()

    # Determine MIME type
    suffix = img_path.suffix.lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    mime = mime_map.get(suffix, "image/jpeg")

    model = genai.GenerativeModel(VISION_MODEL)

    response = model.generate_content(
        [
            SYSTEM_PROMPT,
            {"mime_type": mime, "data": raw},
            "Analyse this image.",
        ],
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            max_output_tokens=300,
        ),
    )

    payload = json.loads(response.text)
    return ImageAnalysis(**payload)


def is_low_confidence(analysis: ImageAnalysis) -> bool:
    """Check if the analysis confidence is below the threshold."""
    return analysis.confidence < CONFIDENCE_THRESHOLD
