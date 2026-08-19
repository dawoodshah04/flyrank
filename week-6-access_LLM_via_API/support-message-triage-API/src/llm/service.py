from test import response
import json 
import os
from pathlib import Path

from openai import OpenAI
from pydantic import ValidationError

from src.llm.schema import TriageRes

PROMPT_VERSION = "triage-v1"
PROMPT_PATH = Path("prompt/triage-v1.md")
QUARANTINE_PATH = Path("logs/quarantine.jsonl")

class LLMService:
    def __init__(self):
        self.client = OpenAI(
            base_url=os.environ["LLM_BASE_URL"],
            api_key=os.environ['LLM_API_KEY'],
            timeout=30.0,
            max_retries=0
        )

        self.model = os.environ["LLM_MODEL"]

    def load_prompt(self) -> str:
        return PROMPT_PATH.read_text(encoding="utf-8")

    def call_model(self,system_prompt:str, user_text:str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_text
                },
            ],
            temperature=0.0
        )

        return response.choices[0].message.content or ""


    def parse_json(self, raw_output:str) -> dict:
        