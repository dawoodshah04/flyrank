"""
Generate ranked image-match suggestions for every embedded post.

Each post is ranked against image-caption embeddings.  Candidates then pass
the deterministic similarity/confidence gates before the semantic guard is
asked to validate the post-to-image pairing.

Usage:  python -m ai.commands.generate_suggestions
"""

import sqlalchemy
from ai.db import get_db
from ai.config import CONFIDENCE_THRESHOLD, SIMILARITY_THRESHOLD
from ai.services.matching import find_matching_images_for_post
from ai.services.mismatch_guard import verify_match


def main() -> None:
    """Generate suggestions for all posts based on image similarity."""
    print("=" * 60)
    print("🔗 Generating Image Suggestions for Posts")
    print("=" * 60)

    db = get_db()

    try:
        # Posts without embeddings cannot be ranked yet.
        posts = db.execute(
            sqlalchemy.text(
                "SELECT id, title, slug, content FROM posts WHERE embedding != '{}'"
            )
        ).fetchall()

        image_count = db.execute(
            sqlalchemy.text(
                "SELECT COUNT(*) FROM images WHERE status = 'tagged' AND embedding != '{}'"
            )
        ).scalar_one()

        print(f"📋 Embedded posts: {len(posts)}, eligible images: {image_count}\n")

        if not posts or not image_count:
            print("⚠  Need embedded posts and analyzed images to generate suggestions")
            return

        created = 0
        rejected = 0

        for post in posts:
            print(f"\n  📝 {post.slug}:")

            candidates = find_matching_images_for_post(
                post.id,
                top_k=5,
                # Keep the top candidates even below the threshold so their
                # rejected guard result is inspectable in the review API.
                threshold=-1.0,
            )

            if not candidates:
                print("     No comparable image embeddings found")
                continue

            for rank, img in enumerate(candidates, 1):
                similarity_score = img["similarity"]
                confidence = img["confidence"]

                if similarity_score < SIMILARITY_THRESHOLD:
                    guard_passed = False
                    guard_reason = (
                        f"Similarity {similarity_score:.3f} is below the "
                        f"required threshold of {SIMILARITY_THRESHOLD:.2f}."
                    )
                elif confidence is None or confidence < CONFIDENCE_THRESHOLD:
                    guard_passed = False
                    readable_confidence = "missing" if confidence is None else f"{confidence:.2f}"
                    guard_reason = (
                        f"Image confidence {readable_confidence} is below the "
                        f"required threshold of {CONFIDENCE_THRESHOLD:.2f}."
                    )
                else:
                    verdict = verify_match(
                        source_subject=post.title,
                        source_caption=post.content,
                        target_subject=img["subject"] or "",
                        target_caption=img["caption"] or "",
                    )
                    guard_passed = verdict["match"]
                    guard_reason = verdict["reason"]

                db.execute(
                    sqlalchemy.text(
                        """
                        INSERT INTO suggestions (id, post_id, image_id, similarity_score,
                                                  guard_passed, guard_reason, rank, status, created_at)
                        VALUES (gen_random_uuid(), :post_id, :image_id, :similarity_score,
                                :guard_passed, :guard_reason, :rank, 'pending', now())
                        ON CONFLICT (post_id, image_id) DO UPDATE SET
                          similarity_score = EXCLUDED.similarity_score,
                          guard_passed = EXCLUDED.guard_passed,
                          guard_reason = EXCLUDED.guard_reason,
                          rank = EXCLUDED.rank
                        """
                    ),
                    {
                        "post_id": post.id,
                        "image_id": img["id"],
                        "similarity_score": similarity_score,
                        "guard_passed": guard_passed,
                        "guard_reason": guard_reason,
                        "rank": rank,
                    },
                )
                db.commit()

                if guard_passed:
                    created += 1
                    print(f"     ✅ rank {rank}: {img['filename']} ({similarity_score:.3f})")
                else:
                    rejected += 1
                    print(f"     ❌ rank {rank}: {img['filename']} — {guard_reason}")

    finally:
        db.close()

    print("\n" + "=" * 60)
    print(f"📊 Created {created} suggestions, rejected {rejected}")
    print("=" * 60)


if __name__ == "__main__":
    main()
