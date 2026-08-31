# AI Image Understanding & Content Matching Engine — Design Document

## Problem Statement

Build a system that analyzes an image library, understands what's in each image, tags it with structured metadata, and matches each image to the right blog post — based on semantic meaning, not filenames or keywords.

**Critical behavior**: When no image is a good match, the system says so instead of guessing. The mismatch guard — a safety layer that rejects wrong matches with explanations — is the production-critical core.

## Architecture

```
┌─────────────────────────────────┐
│     TypeScript (Express)        │
│  API server · Prisma · Zod     │
│  Posts CRUD · Review workflow   │
│  GET /posts/:id/images          │
└────────────┬────────────────────┘
             │
      ┌──────▼──────┐
      │  PostgreSQL  │  ← shared DB
      └──────▲──────┘
             │
┌────────────┴────────────────────┐
│          Python                  │
│  Vision pipeline · Embeddings    │
│  Matching · Mismatch guard       │
│  Batch jobs · Eval               │
└──────────────────────────────────┘
```

## Data Model

- **Images**: id, filename, filepath, status, subject, category, attributes[], caption, confidence, embedding[]
- **Posts**: id, title, slug, content, tags[], embedding[]
- **Suggestions**: id, post_id, image_id, similarity_score, guard_passed, guard_reason, rank, status, review_note
- **AiCallLog**: id, model, call_type, input_ref, tokens_in, tokens_out, cost_usd, success, error

## API Surface

| Endpoint | Method | Description |
|---|---|---|
| `/images` | GET | List images with filtering |
| `/images/:id` | GET | Single image metadata |
| `/posts` | GET | List posts |
| `/posts/:id` | GET | Single post |
| `/posts` | POST | Create post |
| `/posts/:id/images` | GET | **Ranked image suggestions with guard** |
| `/suggestions` | GET | List suggestions |
| `/suggestions/:id` | GET | Inspect suggestion (why suggested/rejected) |
| `/suggestions/:id/approve` | POST | Approve pairing |
| `/suggestions/:id/reject` | POST | Reject pairing |

## Mismatch Guard Rules

1. **Similarity threshold**: Reject if cosine similarity < 0.65
2. **Confidence check**: Reject if vision model confidence < 0.7
3. **Subject conflict**: Reject if subjects are from different animal groups (fox ≠ wolf)
4. **Category mismatch**: Reject obvious mismatches (food image on animal post)

## Non-Goals

- No frontend UI (API + admin table only)
- No multi-model comparison (single vision + single embedding model)
- No real-time vision processing (batch jobs only)
- No user authentication (internal tool)
