"""Download a corpus of ~50 free images from Unsplash for the matching engine.

All images are from Unsplash (https://unsplash.com/license) — free to use.
This script downloads curated images organized by category.

Usage:
    python corpus/download.py
"""

import os
import time
import urllib.request
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent

# Curated Unsplash image URLs organized by category
# Each entry: (filename, unsplash_photo_id, category)
# URL format: https://unsplash.com/photos/{id} → download via ixlib
IMAGES = [
    # ── Red Fox (5 images) ──
    ("red_fox_01.jpg", "https://images.unsplash.com/photo-1474511320723-9a56873571b7?w=640", "fox"),
    ("red_fox_02.jpg", "https://images.unsplash.com/photo-1516934024742-b461fba47600?w=640", "fox"),
    ("red_fox_03.jpg", "https://images.unsplash.com/photo-1504006833117-8886a355efbf?w=640", "fox"),
    ("red_fox_04.jpg", "https://images.unsplash.com/photo-1605386730696-ee82f2fbe45e?w=640", "fox"),
    ("red_fox_05.jpg", "https://images.unsplash.com/photo-1590171466695-988cd93cfe70?w=640", "fox"),

    # ── Gray Wolf (5 images) ──
    ("gray_wolf_01.jpg", "https://images.unsplash.com/photo-1564466809058-bf4114d55352?w=640", "wolf"),
    ("gray_wolf_02.jpg", "https://images.unsplash.com/photo-1546182990-dffeafbe841d?w=640", "wolf"),
    ("gray_wolf_03.jpg", "https://images.unsplash.com/photo-1615812214207-34e3be6812df?w=640", "wolf"),
    ("gray_wolf_04.jpg", "https://images.unsplash.com/photo-1568393691622-c7ba131d63b4?w=640", "wolf"),
    ("gray_wolf_05.jpg", "https://images.unsplash.com/photo-1561731216-c3a4d99437d5?w=640", "wolf"),

    # ── Dog (5 images) ──
    ("dog_01.jpg", "https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=640", "dog"),
    ("dog_02.jpg", "https://images.unsplash.com/photo-1561037404-61cd46aa615b?w=640", "dog"),
    ("dog_03.jpg", "https://images.unsplash.com/photo-1517849845537-4d257902454a?w=640", "dog"),
    ("dog_04.jpg", "https://images.unsplash.com/photo-1534361960057-19889db9621e?w=640", "dog"),
    ("dog_05.jpg", "https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?w=640", "dog"),

    # ── Bear (5 images) ──
    ("bear_01.jpg", "https://images.unsplash.com/photo-1530595467537-0b5996c41f2d?w=640", "bear"),
    ("bear_02.jpg", "https://images.unsplash.com/photo-1589656966895-2f33e7653f6a?w=640", "bear"),
    ("bear_03.jpg", "https://images.unsplash.com/photo-1564760055775-d63b17a55c44?w=640", "bear"),
    ("bear_04.jpg", "https://images.unsplash.com/photo-1525382455947-f319bc05fb35?w=640", "bear"),
    ("bear_05.jpg", "https://images.unsplash.com/photo-1551316679-9c6ae9dec224?w=640", "bear"),

    # ── Deer (5 images) ──
    ("deer_01.jpg", "https://images.unsplash.com/photo-1484406566174-437a19b2e26c?w=640", "deer"),
    ("deer_02.jpg", "https://images.unsplash.com/photo-1485201543483-f06c8d2a8fb4?w=640", "deer"),
    ("deer_03.jpg", "https://images.unsplash.com/photo-1571745544682-143ea663cf2c?w=640", "deer"),
    ("deer_04.jpg", "https://images.unsplash.com/photo-1551189014-fe516aed0e9e?w=640", "deer"),
    ("deer_05.jpg", "https://images.unsplash.com/photo-1547036967-23d11aacaee0?w=640", "deer"),

    # ── Birds (5 images) ──
    ("bird_01.jpg", "https://images.unsplash.com/photo-1444464666168-49d633b86797?w=640", "bird"),
    ("bird_02.jpg", "https://images.unsplash.com/photo-1480044965905-02098d419e96?w=640", "bird"),
    ("bird_03.jpg", "https://images.unsplash.com/photo-1522926193341-e9ffd686c60f?w=640", "bird"),
    ("bird_04.jpg", "https://images.unsplash.com/photo-1555169062-013468b47731?w=640", "bird"),
    ("bird_05.jpg", "https://images.unsplash.com/photo-1470114716159-e389f8712fda?w=640", "bird"),

    # ── Mountains / Landscape (5 images) ──
    ("mountain_01.jpg", "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=640", "mountain"),
    ("mountain_02.jpg", "https://images.unsplash.com/photo-1454496522488-7a8e488e8606?w=640", "mountain"),
    ("mountain_03.jpg", "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=640", "mountain"),
    ("mountain_04.jpg", "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=640", "mountain"),
    ("mountain_05.jpg", "https://images.unsplash.com/photo-1486870591958-9b9d0d1dda99?w=640", "mountain"),

    # ── Ocean / Marine (5 images) ──
    ("ocean_01.jpg", "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=640", "ocean"),
    ("ocean_02.jpg", "https://images.unsplash.com/photo-1439405326854-014607f694d7?w=640", "ocean"),
    ("ocean_03.jpg", "https://images.unsplash.com/photo-1468413253725-0d5181091126?w=640", "ocean"),
    ("ocean_04.jpg", "https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=640", "ocean"),
    ("ocean_05.jpg", "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=640", "ocean"),

    # ── Garden (5 images) ──
    ("garden_01.jpg", "https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=640", "garden"),
    ("garden_02.jpg", "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=640", "garden"),
    ("garden_03.jpg", "https://images.unsplash.com/photo-1588392382834-a891154bca4d?w=640", "garden"),
    ("garden_04.jpg", "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=640", "garden"),
    ("garden_05.jpg", "https://images.unsplash.com/photo-1459411552884-841db9b3cc2a?w=640", "garden"),

    # ── Rainforest / Tropical (5 images) ──
    ("rainforest_01.jpg", "https://images.unsplash.com/photo-1448375240586-882707db888b?w=640", "rainforest"),
    ("rainforest_02.jpg", "https://images.unsplash.com/photo-1502082553048-f009c37129b9?w=640", "rainforest"),
    ("rainforest_03.jpg", "https://images.unsplash.com/photo-1511497584788-876760111969?w=640", "rainforest"),
    ("rainforest_04.jpg", "https://images.unsplash.com/photo-1425913397330-cf8af2ff40a1?w=640", "rainforest"),
    ("rainforest_05.jpg", "https://images.unsplash.com/photo-1440581572325-0bea30075d9d?w=640", "rainforest"),
]


def download():
    """Download all corpus images."""
    print("=" * 60)
    print("📥 Downloading Image Corpus")
    print(f"   Target: {CORPUS_DIR}")
    print(f"   Images: {len(IMAGES)}")
    print("=" * 60)

    stats = {"downloaded": 0, "skipped": 0, "failed": 0}

    for i, (filename, url, category) in enumerate(IMAGES, 1):
        # Create category subdirectory
        category_dir = CORPUS_DIR / category
        category_dir.mkdir(parents=True, exist_ok=True)

        filepath = category_dir / filename

        # Skip if already downloaded
        if filepath.exists() and filepath.stat().st_size > 0:
            print(f"  [{i}/{len(IMAGES)}] ⏭  {category}/{filename} — already exists")
            stats["skipped"] += 1
            continue

        print(f"  [{i}/{len(IMAGES)}] 📥 {category}/{filename}...", end=" ", flush=True)

        try:
            # Add a user-agent header to avoid 403
            req = urllib.request.Request(url, headers={"User-Agent": "ImageMatchingEngine/1.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                data = response.read()
                filepath.write_bytes(data)
                size_kb = len(data) / 1024
                print(f"✅ ({size_kb:.0f} KB)")
                stats["downloaded"] += 1
        except Exception as e:
            print(f"❌ {e}")
            stats["failed"] += 1

        # Small delay to be respectful to Unsplash
        if i < len(IMAGES):
            time.sleep(0.5)

    print("\n" + "=" * 60)
    print("📊 Download Summary")
    print(f"   Downloaded: {stats['downloaded']}")
    print(f"   Skipped:    {stats['skipped']}")
    print(f"   Failed:     {stats['failed']}")
    print("=" * 60)

    if stats["failed"] > 0:
        print("\n⚠  Some downloads failed. Re-run this script to retry.")
        print("   Failed images will be re-attempted on next run.")


if __name__ == "__main__":
    download()
