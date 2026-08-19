import logging
import sys

from fastapi import FastAPI

from src.routes.triage import router as triage_router

# ── Structured logging setup ────────────────────────────────────
# Configure the llm.calls logger to write structured JSON lines to stderr
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    stream=sys.stderr,
)

app = FastAPI(
    title="LLM Support Triage API",
    version="1.0.0",
)

app.include_router(triage_router)


@app.get("/health")
def health():
    return {"status": "ok"}