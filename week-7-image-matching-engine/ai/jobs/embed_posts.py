"""
Generate text embeddings for all posts that don't have one yet.

Usage:  python -m ai.jobs.embed_posts
"""

import sqlalchemy
from ai.db import get_db
from ai.services.embedding import embed_text


def main() -> None:
    """Generate embeddings for posts missing them."""
    print("=" * 60)
    print("📝 Embedding Posts")
    print("=" * 60)

    db = get_db()

    try:
        # Find posts without embeddings
        posts = db.execute(
            sqlalchemy.text(
                "SELECT id, title, content FROM posts WHERE embedding = '{}'"
            )
        ).fetchall()

        if not posts:
            print("✅ All posts already have embeddings")
            return

        print(f"📋 Found {len(posts)} posts to embed\n")

        for i, post in enumerate(posts, 1):
            text = f"{post.title}. {post.content}"

            try:
                # Posts are retrieval queries; image captions use the document
                # role when they are ingested, which makes this ranking
                # asymmetric in the way Gemini's embedding model expects.
                embedding = embed_text(text, task_type="RETRIEVAL_QUERY")

                db.execute(
                    sqlalchemy.text(
                        "UPDATE posts SET embedding = :embedding WHERE id = :id"
                    ),
                    {"embedding": embedding, "id": post.id},
                )
                db.commit()
                print(f"  [{i}/{len(posts)}] ✅ {post.title}")

            except Exception as e:
                print(f"  [{i}/{len(posts)}] ❌ {post.title} — {e}")

    finally:
        db.close()

    print(f"\n📊 Embedded {len(posts)} posts")


if __name__ == "__main__":
    main()
