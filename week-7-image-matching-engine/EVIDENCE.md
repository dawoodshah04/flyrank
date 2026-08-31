# Evidence

One pasted proof per Requirements checkbox. Claims without evidence score as not done.

---

## AI Processing

### ✅ Vision model produces structured output validated against a schema
<!-- Paste: output from ingest_images showing Pydantic validation -->

```
[paste output here after running: python -m ai.jobs.ingest_images]
```

### ✅ Low-confidence classifications are flagged instead of accepted
<!-- Paste: log line showing a low_confidence image -->

```
[paste output showing "Low confidence (0.XX) — flagged"]
```

### ✅ Images processed through batch background job with retries
<!-- Paste: ingest_images output showing batch processing -->

```
[paste batch output here]
```

### ✅ Vision and embedding costs tracked per call
<!-- Paste: SELECT * FROM ai_call_log LIMIT 5 -->

```
[paste query output here]
```

---

## Matching System

### ✅ Image and post embeddings stored; posts return ranked suggestions
<!-- Paste: curl GET /posts/red-fox-behavior/images -->

```
[paste curl output here]
```

### ✅ Semantic matching works — "red fox" matches "Vulpes vulpes"
<!-- Paste: example showing concept matching -->

```
[paste output here]
```

---

## Safety Layer

### ✅ Mismatch guard rejects wolf on fox post
<!-- Paste: suggestion showing guard_passed=false for wolf on fox post -->

```
[paste curl or DB query here]
```

### ✅ Rejections include human-readable explanation
<!-- Paste: guard_reason field from a rejected suggestion -->

```
[paste output here]
```

### ✅ "No confident match" when no image clears the bar
<!-- Paste: GET /posts/:id/images response with match=null -->

```
[paste curl output here]
```

---

## Backend

### ✅ Database models with required indexes
<!-- Paste: prisma schema or migration output -->

```
[paste schema excerpt here]
```

### ✅ API endpoints validated; review workflow exists
<!-- Paste: approve/reject curl examples -->

```
[paste curl output here]
```

---

## Quality & Documentation

### ✅ Labeled eval set measures top-1 precision
<!-- Paste: python -m ai.commands.run_eval output -->

```
[paste eval output here]
```

### ✅ README with architecture explanation
<!-- Link: see README.md -->

README.md committed with architecture diagram, run steps, and precision number.
