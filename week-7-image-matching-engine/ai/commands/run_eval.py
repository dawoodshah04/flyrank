"""Evaluation script: compute top-1 precision on the labeled eval set.

For each labeled pair (post_slug → correct_image_filename):
  1. Look up the post's top suggestion (rank=1, guard_passed=True)
  2. Check if it matches the correct image
  3. Report precision

Usage:
    python -m ai.commands.run_eval
"""

import json
from pathlib import Path

import sqlalchemy

from ai.db import get_db

EVAL_SET_PATH = Path(__file__).resolve().parent.parent / "eval" / "labeled_set.json"


def run():
    """Run evaluation and compute top-1 precision."""
    print("=" * 60)
    print("📊 Running Evaluation — Top-1 Precision")
    print("=" * 60)

    # Load labeled set
    with open(EVAL_SET_PATH) as f:
        labeled_set = json.load(f)

    print(f"📋 Loaded {len(labeled_set)} labeled pairs\n")

    db = get_db()
    correct = 0
    total = 0
    results = []

    try:
        for entry in labeled_set:
            post_slug = entry["post_slug"]
            correct_filename = entry["correct_image_filename"]

            # Get the post
            post = db.execute(
                sqlalchemy.text("SELECT id, title FROM posts WHERE slug = :slug"),
                {"slug": post_slug},
            ).fetchone()

            if not post:
                print(f"  ⚠  Post '{post_slug}' not found in DB — skipping")
                results.append({"post": post_slug, "result": "SKIP", "reason": "post not found"})
                continue

            # Get the top-1 suggestion that passed the guard
            top_suggestion = db.execute(
                sqlalchemy.text(
                    """
                    SELECT s.*, i.filename
                    FROM suggestions s
                    JOIN images i ON s.image_id = i.id
                    WHERE s.post_id = :post_id AND s.guard_passed = true
                    ORDER BY s.rank ASC
                    LIMIT 1
                    """
                ),
                {"post_id": post.id},
            ).fetchone()

            total += 1

            if top_suggestion is None:
                print(f"  ❌ {post_slug}: No suggestion passed guard (expected: {correct_filename})")
                results.append({
                    "post": post_slug,
                    "result": "MISS",
                    "reason": "no suggestion passed guard",
                    "expected": correct_filename,
                })
                continue

            suggested_filename = top_suggestion.filename
            is_correct = suggested_filename == correct_filename

            if is_correct:
                correct += 1
                print(f"  ✅ {post_slug}: {suggested_filename} ← correct!")
            else:
                print(
                    f"  ❌ {post_slug}: got {suggested_filename}, "
                    f"expected {correct_filename} "
                    f"(sim: {top_suggestion.similarity_score:.4f})"
                )

            results.append({
                "post": post_slug,
                "result": "HIT" if is_correct else "MISS",
                "suggested": suggested_filename,
                "expected": correct_filename,
                "similarity": top_suggestion.similarity_score if top_suggestion else None,
            })

    finally:
        db.close()

    # ── Report ──
    print("\n" + "=" * 60)
    if total > 0:
        precision = correct / total
        print(f"🎯 Top-1 Precision: {correct}/{total} = {precision:.0%}")
    else:
        print("🎯 Top-1 Precision: N/A (no evaluable posts)")
    print("=" * 60)

    # Detailed results
    print("\n📋 Detailed Results:")
    for r in results:
        icon = "✅" if r["result"] == "HIT" else "❌" if r["result"] == "MISS" else "⏭"
        print(f"  {icon} {r['post']}: {r['result']}")

    return results


if __name__ == "__main__":
    run()
