import json
import re
from pyparsing import Any
from app.core.logger_config import logger


def _to_text(content: Any) -> str:
    # Normalize content to string for consistent generator typing
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                # common LangChain content dicts may have 'text'
                text = part.get("text")
                if isinstance(text, str):
                    parts.append(text)
                else:
                    # best-effort fallback
                    parts.append(str(part))
            else:
                parts.append(str(part))
        return "".join(parts)
    return content if isinstance(content, str) else str(content)


def clean_and_parse_ai_output(text: str):
    # Step 1: Remove markdown-style code fences
    cleaned = re.sub(r"```json|```", "", text).strip()

    # Step 2: Parse the JSON
    try:
        parsed = json.loads(cleaned)
        return parsed
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}", exc_info=True)
        return None
