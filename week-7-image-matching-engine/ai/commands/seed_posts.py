"""
Seed sample blog posts into the database.

Usage:  python -m ai.commands.seed_posts
"""

import sqlalchemy
from ai.db import get_db

SAMPLE_POSTS = [
    {
        "title": "Red Fox Behavior in the Wild",
        "slug": "red-fox-behavior",
        "content": "The red fox (Vulpes vulpes) is a remarkable creature known for its cunning and adaptability. Found across the Northern Hemisphere, red foxes are skilled hunters that primarily feed on small mammals, birds, and berries. Their distinctive red-orange coat and bushy tail make them one of the most recognizable wild animals.",
        "tags": ["fox", "wildlife", "nature", "mammals"],
    },
    {
        "title": "Gray Wolf Pack Dynamics",
        "slug": "gray-wolf-pack-dynamics",
        "content": "Gray wolves (Canis lupus) are highly social animals that live in packs with complex hierarchies. Pack dynamics revolve around the alpha pair, and wolves communicate through body language, vocalizations, and scent marking. Understanding wolf behavior is crucial for conservation efforts.",
        "tags": ["wolf", "wildlife", "nature", "mammals"],
    },
    {
        "title": "Best Dog Breeds for Families",
        "slug": "best-dog-breeds-families",
        "content": "Choosing the right dog breed for your family involves considering temperament, size, and energy levels. Golden Retrievers, Labrador Retrievers, and Beagles are among the most popular family-friendly breeds, known for their gentle nature and love of children.",
        "tags": ["dog", "pets", "family", "breeds"],
    },
    {
        "title": "Mountain Hiking Adventures",
        "slug": "mountain-hiking-adventures",
        "content": "Mountain hiking offers breathtaking views and a unique connection with nature. From the Rockies to the Alps, each mountain range presents different challenges and rewards. Proper preparation, including gear selection and fitness training, is essential for a safe and enjoyable experience.",
        "tags": ["mountain", "hiking", "nature", "adventure"],
    },
    {
        "title": "Ocean Conservation Efforts",
        "slug": "ocean-conservation-efforts",
        "content": "Our oceans face unprecedented threats from pollution, overfishing, and climate change. Marine conservation efforts focus on protecting coral reefs, reducing plastic waste, and establishing marine protected areas to preserve biodiversity for future generations.",
        "tags": ["ocean", "conservation", "marine", "environment"],
    },
    {
        "title": "Backyard Garden Design Ideas",
        "slug": "backyard-garden-design",
        "content": "Creating a beautiful backyard garden starts with understanding your local climate and soil conditions. From flower beds to vegetable patches, thoughtful garden design combines aesthetics with functionality, providing a peaceful retreat right at home.",
        "tags": ["garden", "design", "plants", "home"],
    },
    {
        "title": "Bear Watching in National Parks",
        "slug": "bear-watching-national-parks",
        "content": "Bear watching is a thrilling wildlife experience available in many national parks. Both black bears and grizzly bears can be observed in their natural habitats, but safety protocols must be strictly followed to protect both visitors and these magnificent creatures.",
        "tags": ["bear", "wildlife", "national-parks", "nature"],
    },
    {
        "title": "Birdwatching for Beginners",
        "slug": "birdwatching-beginners",
        "content": "Birdwatching is a relaxing hobby that connects you with nature. Starting with a good pair of binoculars and a field guide, beginners can quickly learn to identify common species by their plumage, songs, and behaviors. Local parks and wetlands are great starting points.",
        "tags": ["bird", "birdwatching", "nature", "hobby"],
    },
]


def main() -> None:
    """Seed posts into the database."""
    print("=" * 60)
    print("🌱 Seeding Sample Posts")
    print("=" * 60)

    db = get_db()
    created = 0
    skipped = 0

    try:
        for post in SAMPLE_POSTS:
            # Check if post already exists
            existing = db.execute(
                sqlalchemy.text("SELECT id FROM posts WHERE slug = :slug"),
                {"slug": post["slug"]},
            ).fetchone()

            if existing:
                print(f"  ⏭  {post['slug']} — already exists")
                skipped += 1
                continue

            db.execute(
                sqlalchemy.text(
                    """
                    INSERT INTO posts (id, title, slug, content, tags, created_at, updated_at)
                    VALUES (gen_random_uuid(), :title, :slug, :content, :tags, now(), now())
                    """
                ),
                {
                    "title": post["title"],
                    "slug": post["slug"],
                    "content": post["content"],
                    "tags": post["tags"],
                },
            )
            db.commit()
            print(f"  ✅ {post['slug']} — created")
            created += 1

    finally:
        db.close()

    print(f"\n📊 Seeded {created} posts, skipped {skipped}")


if __name__ == "__main__":
    main()
