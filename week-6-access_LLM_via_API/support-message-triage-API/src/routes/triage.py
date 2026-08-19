import os
import logging

import openai
from fastapi import APIRouter, HTTPException

from src.llm.schema import TriageReq, TriageRes
from src.llm.service import LLMService

logger = logging.getLogger("llm.calls")
router = APIRouter()
llm_service = LLMService()


@router.post("/triage", response_model=TriageRes)
def triage(req: TriageReq):
    # ── Kill switch ──────────────────────────────────────────────
    if os.getenv("LLM_ENABLED", "true").lower() == "false":
        logger.info('{"event": "llm_kill_switch", "action": "returning_503"}')
        raise HTTPException(
            status_code=503,
            detail="LLM service is temporarily disabled. Set LLM_ENABLED=true to re-enable.",
        )

    try:
        result = llm_service.classify(req.text)
        return result

    except openai.APITimeoutError:
        raise HTTPException(
            status_code=504,
            detail="LLM request timed out after 30 seconds. Please try again.",
        )
    except openai.AuthenticationError as e:
        raise HTTPException(
            status_code=401,
            detail=f"LLM authentication failed: {e.message}",
        )
    except openai.RateLimitError:
        raise HTTPException(
            status_code=429,
            detail="LLM rate limit exceeded after retries. Please try again later.",
        )
    except openai.APIStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"LLM provider error (status {e.status_code}): {e.message}",
        )
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        )
