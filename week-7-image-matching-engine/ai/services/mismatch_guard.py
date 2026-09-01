"""Mismatch guard — use Gemini to validate a post-to-image pairing."""

import json
import google.generativeai as genai

from ai.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

GUARD_MODEL = "gemini-2.0-flash"

SYSTEM_PROMPT = """You are a visual-matching quality guard.
Given a blog post and an image description, decide whether the image is a genuine
visual match for that post.

Return JSON: {"match": true/false, "reason": "..."}.
Be strict: only return true if the images share clear visual or semantic similarity.
For example, a wolf and a fox are NOT a match even though they are both canines."""


def verify_match(
    source_subject: str,
    source_caption: str,
    target_subject: str,
    target_caption: str,
) -> dict:
    """
    Ask the vision model to confirm whether two images are a genuine match.
    Returns {"match": bool, "reason": str}.
    """
    model = genai.GenerativeModel(GUARD_MODEL)

    prompt = (
        f"Blog post title: '{source_subject}'\n"
        f"Blog post excerpt: '{source_caption}'\n"
        f"Image subject: '{target_subject}'\n"
        f"Image caption: '{target_caption}'\n\n"
        "Is this image a good visual match for this blog post? Consider whether "
        "the image depicts the post's primary subject, not merely a related category."
    )

    response = model.generate_content(
        [SYSTEM_PROMPT, prompt],
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            max_output_tokens=256,
        ),
    )

    try:
        result = json.loads(response.text)
        return {
            "match": bool(result.get("match", False)),
            "reason": str(result.get("reason", "")),
        }
    except (json.JSONDecodeError, AttributeError):
        return {"match": False, "reason": "Failed to parse guard response"}
