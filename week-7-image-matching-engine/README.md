# AI Image Understanding & Content Matching Engine

An AI-powered system that analyzes an image library, tags each image with structured metadata, and matches the right image to the right blog post — based on semantic meaning, not filenames. **When no image is good enough, the system says so instead of guessing.**

## Architecture

```
Images ──(batch job)──→ Gemini Flash ──→ {tags, caption, confidence} ──→ images table
                                          │ embed(caption) ──────────→ image vectors
Posts ─────────────────→ embed(content) ──────────────────────────────→ post vectors

GET /posts/:id/images
  → Cosine Similarity Ranking (image_vectors × post_vector)
  → Mismatch Guard (tags + threshold + confidence)
  │ ✅ Suggested image (ranked, explained)
  │ ❌ "No confident match" + explanation
  → Review API: approve / reject
```

### Stack

| Layer | Technology |
|---|---|
| API Server | TypeScript · Express · Zod |
| Database | PostgreSQL (Prisma ORM) |
| Vision Model | Python · Gemini Flash (free tier) |
| Embeddings | Python · Gemini text-embedding-004 |
| Matching | Python · numpy cosine similarity |
| Mismatch Guard | Python · Pydantic |

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- Gemini API key (free — [get one here](https://aistudio.google.com/apikey))

### Setup

```bash
# 1. Clone and configure
git clone <repo-url>
cp .env.example .env
# Edit .env — add your GEMINI_API_KEY

# 2. Start PostgreSQL
docker compose up -d

# 3. Setup TypeScript server
cd server
npm install
npx prisma migrate dev --name init
cd ..

# 4. Setup Python environment
cd ai
pip install -r requirements.txt
cd ..

# 5. Download image corpus (~50 images)
python corpus/download.py

# 6. Seed blog posts
python -m ai.commands.seed_posts

# 7. Process images (vision + embeddings)
python -m ai.jobs.ingest_images

# 8. Embed posts
python -m ai.jobs.embed_posts

# 9. Generate suggestions
python -m ai.commands.generate_suggestions

# 10. Start API server
cd server && npm run dev
```

### Test the system

```bash
# Get image suggestions for the fox post
curl http://localhost:3000/posts/red-fox-behavior/images | jq

# Run evaluation
python -m ai.commands.run_eval
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/images` | List images (filter by status, category) |
| GET | `/images/:id` | Get image metadata |
| GET | `/posts` | List posts |
| GET | `/posts/:id` | Get post by ID or slug |
| POST | `/posts` | Create post |
| GET | `/posts/:id/images` | **Ranked image suggestions with guard** |
| GET | `/suggestions` | List all suggestions |
| GET | `/suggestions/:id` | Inspect why suggested/rejected |
| POST | `/suggestions/:id/approve` | Approve pairing |
| POST | `/suggestions/:id/reject` | Reject pairing |

## The Mismatch Guard

The core safety layer that prevents wrong matches:

| Rule | What it checks |
|---|---|
| Similarity threshold | Cosine similarity must be ≥ 0.65 |
| Confidence check | Vision model confidence must be ≥ 0.7 |
| Subject conflict | Fox ≠ wolf, dog ≠ wolf, etc. |
| Category mismatch | Animal image ≠ food post |

## Evaluation

```
Top-1 Precision: [run python -m ai.commands.run_eval to measure]
```

## Limitations

- Corpus is small (~50 images) — real systems need thousands
- Single vision model — no ensemble or fallback
- Thresholds are tuned on a small eval set
- No real-time processing — batch jobs only
- No authentication on the API

## License

MIT
