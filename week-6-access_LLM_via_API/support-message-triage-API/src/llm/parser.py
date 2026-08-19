import json 

def parse_json_obj(text:str) -> dict:
    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

            text = "\n".join(lines).strip()

        if text.lower().startswith('json'):
            text = text[4:].strip()


    start = text.find('{')
    end = text.rfind('}')

    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON obj found in model output")

    return json.loads(text[start: end+1])