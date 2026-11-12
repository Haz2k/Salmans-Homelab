import base64
import json
import mimetypes
import os
import re

from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

EXTRACTION_PROMPT = """You are reading a purchase receipt for a small business expense tracker.
Return ONLY a single JSON object, no other text, no markdown fences, matching exactly this shape:

{{
  "merchant": string or null,
  "purchase_date": "YYYY-MM-DD" or null,
  "items": [{{"description": string, "quantity": number, "price": number}}],
  "subtotal": number or null,
  "tax": number or null,
  "total": number or null,
  "suggested_category": one of {categories} or null
}}

Rules:
- "price" is the line's total price (quantity already applied), not a per-unit price.
- If you can't read a field confidently, use null rather than guessing.
- Only pick suggested_category from the exact list given; if nothing fits well, use null.
- Return valid JSON only.
"""


def _media_type_for(filename: str) -> str:
    guessed, _ = mimetypes.guess_type(filename)
    if guessed in ("image/jpeg", "image/png", "image/webp", "image/gif", "application/pdf"):
        return guessed
    return "image/jpeg"


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    return match.group(1) if match else text


def extract_receipt(file_path: str, filename: str, category_names: list[str]) -> dict:
    """Calls Claude with the receipt image/PDF and returns parsed extraction JSON.
    Raises ValueError if the model doesn't return parseable JSON.
    """
    with open(file_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")

    media_type = _media_type_for(filename)
    block_type = "document" if media_type == "application/pdf" else "image"

    prompt = EXTRACTION_PROMPT.format(categories=json.dumps(category_names))

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": block_type,
                        "source": {"type": "base64", "media_type": media_type, "data": data},
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )

    raw_text = "".join(block.text for block in response.content if block.type == "text")
    cleaned = _strip_code_fence(raw_text)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model did not return valid JSON: {raw_text[:500]}") from exc

    return parsed
