"""
Scan the corpus directory for images, analyse each with the vision model,
generate embeddings, and upsert rows into the *images* table.

Usage:  python -m ai.jobs.ingest_images
"""

import sqlalchemy
from pathlib import Path

from ai.config import CORPUS_DIR, CONFIDENCE_THRESHOLD
from ai.db import get_db
from ai.services.vision import analyse_image, is_low_confidence
from ai.services.embedding import embed_text

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

MAX_RETRIES = 3


def _find_images(directory: Path) -> list[Path]:
    """Recursively find all image files in corpus subdirectories."""
    images = []
    if not directory.exists():
        return images
    for p in sorted(directory.rglob("*")):
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS:
            images.append(p)
    return images


def main() -> None:
    """Ingest images from the corpus into the database."""
    print("=" * 60)
    print("📸 Ingesting Images from Corpus")
    print(f"   Corpus: {CORPUS_DIR}")
    print("=" * 60)

    images = _find_images(CORPUS_DIR)
    print(f"📋 Found {len(images)} images\n")

    if not images:
        print("⚠  No images found in corpus. Run 'python corpus/download.py' first.")
        return

    db = get_db()
    stats = {"ingested": 0, "skipped": 0, "low_confidence": 0, "failed": 0}

    try:
        for i, img_path in enumerate(images, 1):
            filename = img_path.name
            filepath = str(img_path.relative_to(CORPUS_DIR))

            # Skip if already ingested
            existing = db.execute(
                sqlalchemy.text("SELECT id FROM images WHERE filename = :filename"),
                {"filename": filename},
            ).fetchone()

            if existing:
                print(f"  [{i}/{len(images)}] ⏭  {filepath} — already ingested")
                stats["skipped"] += 1
                continue

            # Analyse image with retries
            analysis = None
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    analysis = analyse_image(img_path)
                    break
                except Exception as e:
                    if attempt == MAX_RETRIES:
                        print(f"  [{i}/{len(images)}] ❌ {filepath} — failed after {MAX_RETRIES} retries: {e}")
                        stats["failed"] += 1
                    else:
                        print(f"  [{i}/{len(images)}] ⚠  Retry {attempt}/{MAX_RETRIES} for {filepath}: {e}")

            if analysis is None:
                continue

            # Check confidence
            status = "tagged"
            if is_low_confidence(analysis):
                status = "low_confidence"
                stats["low_confidence"] += 1
                print(f"  [{i}/{len(images)}] ⚠  {filepath} — Low confidence ({analysis.confidence:.2f}) — flagged")

            # Generate embedding from caption
            try:
                embedding = embed_text(analysis.caption)
            except Exception as e:
                print(f"  [{i}/{len(images)}] ❌ {filepath} — embedding failed: {e}")
                stats["failed"] += 1
                continue

            # Insert into database
            db.execute(
                sqlalchemy.text(
                    """
                    INSERT INTO images (id, filename, filepath, status, subject, category,
                                        attributes, caption, confidence, embedding,
                                        created_at, updated_at)
                    VALUES (gen_random_uuid(), :filename, :filepath, :status, :subject,
                            :category, :attributes, :caption, :confidence, :embedding,
                            now(), now())
                    """
                ),
                {
                    "filename": filename,
                    "filepath": filepath,
                    "status": status,
                    "subject": analysis.subject,
                    "category": analysis.category,
                    "attributes": analysis.attributes,
                    "caption": analysis.caption,
                    "confidence": analysis.confidence,
                    "embedding": embedding,
                },
            )
            db.commit()

            status_icon = "✅" if status == "tagged" else "⚠ "
            print(
                f"  [{i}/{len(images)}] {status_icon} {filepath} — "
                f"{analysis.subject} ({analysis.confidence:.2f})"
            )
            stats["ingested"] += 1

    finally:
        db.close()

    print("\n" + "=" * 60)
    print("📊 Ingestion Summary")
    print(f"   Ingested:       {stats['ingested']}")
    print(f"   Skipped:        {stats['skipped']}")
    print(f"   Low confidence: {stats['low_confidence']}")
    print(f"   Failed:         {stats['failed']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
