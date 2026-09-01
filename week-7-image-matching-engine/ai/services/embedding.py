"""Embedding service — generate text embeddings using Google Gemini."""

import google.generativeai as genai
import numpy as np

from ai.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

EMBEDDING_MODEL = "models/text-embedding-004"


def embed_text(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
    """Return the embedding vector for *text* using the requested retrieval role."""
    if not text.strip():
        raise ValueError("Cannot embed empty text")

    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=text,
        task_type=task_type,
    )
    return result["embedding"]


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Return embedding vectors for a batch of texts."""
    embeddings = []
    for text in texts:
        embeddings.append(embed_text(text))
    return embeddings


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a_arr = np.asarray(a, dtype=float)
    b_arr = np.asarray(b, dtype=float)
    if a_arr.shape != b_arr.shape:
        raise ValueError("Embedding vectors must have the same dimensions")
    denominator = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    return float(np.dot(a_arr, b_arr) / denominator) if denominator else 0.0
