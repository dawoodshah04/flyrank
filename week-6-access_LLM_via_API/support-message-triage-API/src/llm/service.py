import json
import logging
import random
import time
from pathlib import Path

import openai
from pydantic import ValidationError

from src.llm.client import client, MODEL
from src.llm.schema import TriageRes

logger = logging.getLogger("llm.calls")

PROMPT_VERSION = "triage-v1"
PROMPT_PATH = Path("prompts/triage-v1.md")
QUARANTINE_PATH = Path("logs/quarantine.jsonl")

MAX_RETRIES = 2  # 2 retries = 3 total attempts
BASE_DELAYS = [1.0, 2.0, 4.0]


class LLMService:
    def __init__(self):
        self.client = client
        self.model = MODEL

    def load_prompt(self) -> str:
        return PROMPT_PATH.read_text(encoding="utf-8")

    def _call_with_retry(self, messages: list[dict], temperature: float = 0.0):
        """Call the LLM with retry logic for transient failures.

        Retries on: timeouts, 429 (rate limit), 5xx (server errors).
        Never retries on: 400, 401, 403 (client errors).
        Uses exponential backoff with jitter: 1s, 2s, 4s + random 0-0.5s.
        """
        last_exception = None

        for attempt in range(MAX_RETRIES + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                )
                return response

            except openai.APITimeoutError as e:
                last_exception = e
                if attempt < MAX_RETRIES:
                    delay = BASE_DELAYS[attempt] + random.uniform(0, 0.5)
                    logger.warning(
                        json.dumps({
                            "event": "llm_retry",
                            "reason": "timeout",
                            "attempt": attempt + 1,
                            "delay_s": round(delay, 2),
                        })
                    )
                    time.sleep(delay)
                else:
                    raise

            except openai.RateLimitError as e:
                last_exception = e
                if attempt < MAX_RETRIES:
                    # Respect Retry-After header if present
                    retry_after = None
                    if e.response and e.response.headers:
                        retry_after_str = e.response.headers.get("Retry-After")
                        if retry_after_str:
                            try:
                                retry_after = float(retry_after_str)
                            except (ValueError, TypeError):
                                pass
                    delay = retry_after if retry_after else BASE_DELAYS[attempt] + random.uniform(0, 0.5)
                    logger.warning(
                        json.dumps({
                            "event": "llm_retry",
                            "reason": "rate_limit_429",
                            "attempt": attempt + 1,
                            "delay_s": round(delay, 2),
                            "used_retry_after": retry_after is not None,
                        })
                    )
                    time.sleep(delay)
                else:
                    raise

            except openai.APIStatusError as e:
                # Never retry client errors (400, 401, 403)
                if e.status_code < 500:
                    logger.error(
                        json.dumps({
                            "event": "llm_non_retryable_error",
                            "status_code": e.status_code,
                            "message": str(e),
                        })
                    )
                    raise
                # Retry 5xx server errors
                last_exception = e
                if attempt < MAX_RETRIES:
                    delay = BASE_DELAYS[attempt] + random.uniform(0, 0.5)
                    logger.warning(
                        json.dumps({
                            "event": "llm_retry",
                            "reason": f"server_error_{e.status_code}",
                            "attempt": attempt + 1,
                            "delay_s": round(delay, 2),
                        })
                    )
                    time.sleep(delay)
                else:
                    raise

        raise last_exception  # Safety net — should not reach here

    def call_model(self, system_prompt: str, user_text: str) -> tuple:
        """Call the LLM and return (raw_content, usage, duration_ms)."""
        start = time.perf_counter()

        response = self._call_with_retry(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
            temperature=0.0,
        )

        duration_ms = round((time.perf_counter() - start) * 1000)
        usage = response.usage
        content = response.choices[0].message.content or ""

        return content, usage, duration_ms

    def parse_json(self, raw_output: str) -> dict:
        """Extract and parse JSON from model output, handling markdown fences."""
        text = raw_output.strip()

        # Remove Markdown code fences
        if text.startswith("```"):
            lines = text.splitlines()

            if lines and lines[0].startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            text = "\n".join(lines).strip()

            if text.lower().startswith("json"):
                text = text[4:].strip()

        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1:
            raise ValueError("No JSON obj found in model output")

        json_text = text[start : end + 1]

        return json.loads(json_text)

    def validate_output(self, raw_output: str) -> TriageRes:
        parsed = self.parse_json(raw_output)
        return TriageRes.model_validate(parsed)

    def quarantine(self, input_text: str, raw_output: str, error: str) -> None:
        """Log failed outputs to quarantine file for later review."""
        QUARANTINE_PATH.parent.mkdir(parents=True, exist_ok=True)

        record = {
            "input": input_text,
            "raw_output": raw_output,
            "error": error,
            "prompt_version": PROMPT_VERSION,
        }

        with QUARANTINE_PATH.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record) + "\n")

    def repair(self, user_text: str, previous_output: str, validation_error: str) -> tuple:
        """Attempt to repair invalid model output. Returns (content, usage, duration_ms)."""
        system_prompt = self.load_prompt()

        repair_message = (
            "Your previous answer was rejected because it did not match "
            "the required output schema.\n\n"
            f"Validation error:\n{validation_error}\n\n"
            f"Previous answer:\n{previous_output}\n\n"
            "Return ONLY corrected JSON matching the required schema.\n"
            "Do not explain your answer.\n"
            "Do not use Markdown.\n"
            "Do not add extra fields."
        )

        return self.call_model(
            system_prompt=system_prompt,
            user_text=repair_message,
        )

    def _log_call(self, usage, duration_ms: int, needed_repair: bool, status: str) -> None:
        """Write one structured log line per LLM call."""
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0

        logger.info(
            json.dumps({
                "event": "llm_call",
                "prompt_version": PROMPT_VERSION,
                "model": self.model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "duration_ms": duration_ms,
                "needed_repair": needed_repair,
                "status": status,
            })
        )

    def classify(self, user_text: str) -> TriageRes:
        """Classify a support message. Attempts repair once on invalid output."""
        system_prompt = self.load_prompt()

        raw_output, usage, duration_ms = self.call_model(
            system_prompt=system_prompt,
            user_text=user_text,
        )

        try:
            result = self.validate_output(raw_output)
            self._log_call(usage, duration_ms, needed_repair=False, status="success")
            return result

        except (ValueError, json.JSONDecodeError, ValidationError) as first_error:
            repaired_output, repair_usage, repair_duration = self.repair(
                user_text=user_text,
                previous_output=raw_output,
                validation_error=str(first_error),
            )

            total_duration = duration_ms + repair_duration

            try:
                result = self.validate_output(repaired_output)
                self._log_call(repair_usage, total_duration, needed_repair=True, status="success")
                return result

            except (ValueError, json.JSONDecodeError, ValidationError) as second_error:
                self.quarantine(
                    input_text=user_text,
                    raw_output=repaired_output,
                    error=str(second_error),
                )
                self._log_call(repair_usage, total_duration, needed_repair=True, status="error")
                raise ValueError(
                    "The model could not produce valid output after one repair attempt."
                )