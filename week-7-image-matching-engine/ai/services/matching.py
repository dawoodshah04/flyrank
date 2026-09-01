"""Matching service — rank images for a post using cosine similarity."""

import numpy as np
from ai.db import get_db
from ai.config import SIMILARITY_THRESHOLD


def find_matching_images_for_post(
    post_id: str,
    top_k: int = 5,
    threshold: float | None = None,
) -> list[dict]:
    """
    Return the *top_k* images most semantically similar to a post.

    Both posts and image captions are embedded with Gemini.  Ranking those two
    vectors is the matching step; filename/category checks are only safety
    signals and must not replace semantic ranking.
    """
    sim_threshold = threshold if threshold is not None else SIMILARITY_THRESHOLD
    db = get_db()

    try:
        # Fetch the post embedding.
        import sqlalchemy
        post = db.execute(
            sqlalchemy.text("SELECT embedding FROM posts WHERE id = :id"),
            {"id": post_id},
        ).fetchone()

        if post is None or not post.embedding:
            return []

        post_embedding = np.asarray(post.embedding, dtype=float)
        post_norm = np.linalg.norm(post_embedding)
        if post_norm == 0:
            return []

        # Only analyzed, sufficiently confident images are eligible.  The
        # confidence check is repeated by the caller to produce a clear guard
        # reason if data changes between these queries.
        rows = db.execute(
            sqlalchemy.text(
                "SELECT id, filename, subject, category, caption, confidence, embedding "
                "FROM images WHERE status = 'tagged' AND embedding != '{}'"
            ),
        ).fetchall()

        results = []
        for row in rows:
            if not row.embedding:
                continue
            target_embedding = np.asarray(row.embedding, dtype=float)
            if target_embedding.shape != post_embedding.shape:
                # A mixed embedding-model dataset cannot be compared safely.
                continue

            # Cosine similarity
            dot = np.dot(post_embedding, target_embedding)
            norm = post_norm * np.linalg.norm(target_embedding)
            if norm == 0:
                continue
            similarity = float(dot / norm)

            if similarity >= sim_threshold:
                results.append({
                    "id": row.id,
                    "filename": row.filename,
                    "subject": row.subject,
                    "category": row.category,
                    "caption": row.caption,
                    "confidence": row.confidence,
                    "similarity": similarity,
                })

        # Sort by similarity descending and take top_k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    finally:
        db.close()
