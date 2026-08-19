# LLM Support Triage API

A FastAPI service that classifies customer support messages into categories (`billing`, `bug`, `feature`, `other`) with urgency levels (`low`, `normal`, `high`) using an LLM.

## Setup

```bash
# Clone the repo
git clone <repo-url>
cd support-message-triage-API

# Create venv and install dependencies
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate         # Windows
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your actual API key

# Run the server
uvicorn src.main:app --reload
```

## API Endpoints

### `POST /triage`

Classify a support message.

**Request:**
```json
{
  "text": "My invoice has two charges for the same subscription."
}
```

**Response:**
```json
{
  "category": "billing",
  "urgency": "normal",
  "confidence": 0.95,
  "reason": "The customer reports a duplicate subscription charge."
}
```

### `GET /health`

Health check endpoint. Returns `{"status": "ok"}`.

## Environment Variables

| Variable        | Description                                              | Default  |
|-----------------|----------------------------------------------------------|----------|
| `LLM_BASE_URL`  | LLM provider base URL                                    | Required |
| `LLM_API_KEY`   | API key for the LLM provider                             | Required |
| `LLM_MODEL`     | Model identifier                                         | Required |
| `LLM_ENABLED`   | Kill switch — set to `false` to disable LLM calls (503) | `true`   |

## Retry Strategy

**SDK auto-retries are disabled** (`max_retries=0`). Retries are handled manually in `LLMService._call_with_retry()` for full control over which failures are retried.

| Condition       | Retried? | Reason                                             |
|-----------------|----------|----------------------------------------------------|
| Timeout         | ✅ Yes    | Transient network issue                            |
| 429 Rate Limit  | ✅ Yes    | Respects `Retry-After` header when present         |
| 5xx Server Error| ✅ Yes    | Provider-side transient failure                    |
| 400 Bad Request | ❌ Never  | Request is malformed, won't fix itself             |
| 401 Unauthorized| ❌ Never  | Bad key will still be a bad key in 4 seconds       |
| 403 Forbidden   | ❌ Never  | Permissions won't change between retries           |

**Backoff:** Exponential with jitter — `1s`, `2s`, `4s` base delays + random `0–0.5s`.

**Max attempts:** 3 total (1 initial + 2 retries).

Each user request makes at most 3 LLM calls (plus up to 3 more if a repair attempt is needed). Silent SDK defaults are disabled explicitly to avoid surprise retries.

## Kill Switch

Set `LLM_ENABLED=false` to disable the LLM entirely. The endpoint returns **503** immediately with zero model calls. Use this during:

- Provider outages
- Cost spikes
- Model misbehavior

Anyone with env var access can toggle it without redeploying.

## Structured Logging

Every LLM call produces a structured JSON log line to stderr with:

```json
{
  "event": "llm_call",
  "prompt_version": "triage-v1",
  "model": "meta-llama/llama-3.1-8b-instruct:free",
  "input_tokens": 512,
  "output_tokens": 87,
  "duration_ms": 1423,
  "needed_repair": false,
  "status": "success"
}
```

Use these logs to answer _"how much will this cost at 10,000 calls/day."_

## Error Handling

| Status | Meaning                                          |
|--------|--------------------------------------------------|
| 422    | Invalid input or model output unparseable after repair |
| 401    | LLM authentication failed (bad API key)          |
| 429    | Rate limited after retries                        |
| 502    | LLM provider error                                |
| 503    | LLM disabled via kill switch                      |
| 504    | LLM request timed out after 30s                   |

## Project Structure

```
src/
  main.py          — FastAPI app entry point + logging config
  llm/
    client.py      — Shared OpenAI client (single source of truth)
    schema.py      — Pydantic models for request/response
    service.py     — LLM service with retry, logging, repair
    parser.py      — JSON extraction from model output
    test.py        — Quick connectivity test
  routes/
    triage.py      — /triage endpoint with kill switch + error handling
prompts/
  triage-v1.md     — System prompt for classification
logs/
  quarantine.jsonl — Failed outputs for review
evals/
  cases.json       — Evaluation test cases
```
