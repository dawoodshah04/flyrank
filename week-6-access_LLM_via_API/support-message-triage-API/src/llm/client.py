"""Shared OpenAI client — single source of truth for LLM configuration.

Retry strategy: SDK auto-retries are DISABLED (max_retries=0).
Retries are handled manually in LLMService._call_with_retry() with
exponential backoff + jitter (1s, 2s, 4s), max 3 total attempts.
Only timeouts, 429, and 5xx are retried. 400/401/403 are never retried.
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.environ["LLM_BASE_URL"],
    api_key=os.environ["LLM_API_KEY"],
    timeout=30.0,
    max_retries=0,
)

MODEL = os.environ["LLM_MODEL"]