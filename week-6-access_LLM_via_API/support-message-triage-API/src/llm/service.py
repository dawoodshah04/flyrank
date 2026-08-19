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
        text = raw_output.strip()

        #Remove Markdown code fences
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
        end = text.rfind('}')

        if start == -1 or end == -1:
            raise ValueError("No JSON obj found in model output")

        json_text = text[start:end+1]

        return json.loads(json_text)


    def validate_output(self, raw_output:str)-> TriageRes:
        parsed = self.parse_json(raw_output)

        return TriageRes.model_validate(parsed)


    
    def quaratine(self,input_text:str,raw_output:str,error:str)->None:

        QUARANTINE_PATH.parent.mkdir(parents=True,exist_ok=True)

        record = {
            "input": input_text,
            "raw_output": raw_output,
            "error": error,
            "prompt_version": PROMPT_VERSION
        }


        with QUARANTINE_PATH.open("a",encoding="utf-8") as file:
            file.write(json.dumps(record)+"\n")


    def repair(self,user_text:str,previous_output:str,validation_error:str
    )->str:
        system_prompt = self.load_prompt()

        repair_message = f"""
        Your previous answer was rejected because it did not match
        the required output schema.

        Validation error:
         {validation_error}

        Previous answer:
        {previous_output}

        Return ONLY corrected JSON matching the required schema.

        Do not explain your answer.
        Do not use Markdown.
        Do not add extra fields.
        """ 

        return self.call_model(
            system_prompt=system_prompt,
            user_text=repair_message
        )

    
    def classify(self,user_text:str) -> TriageRes:
        system_prompt = self.load_prompt()

        raw_output = self.call_model(
            system_prompt=system_prompt,
            user_text=user_text
        )


        try:
            return self.validate_output(raw_output)

        except (ValueError, json.JSONDecodeError,ValidationError) as firstError:

            repaired_output = self.repair(
                user_text=user_text,
                previous_output=raw_output,
                validation_error=ValidationError
            )


            try:
                return self.validate_output(repaired_output)

            except (ValueError, json.JSONDecodeError,ValidationError) as secondError:

                  self.quaratine(
                input_text=user_text,
                raw_output=repaired_output,
                error=str(secondError)
            )
             
            raise ValueError(
                    "The model could not produce valid output after one repair attempt."
                )