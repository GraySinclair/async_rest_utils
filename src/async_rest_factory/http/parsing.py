from __future__ import annotations

import json
from typing import Any


def parse_response_body(
    body_text: str,
    *,
    content_type: str | None = None,
    max_preview_chars: int = 2_000,
) -> Any:
    """
    Parse an HTTP response body as JSON.

    Returns:
        - {} when the body is empty
        - parsed JSON when the body is valid JSON
        - a structured diagnostic dictionary when JSON parsing fails

    The failure shape is intentionally consistent so HttpResponseError can
    display useful details without requiring extra print/debug code.
    """

    if not body_text:
        return {}

    try:
        return json.loads(body_text)

    except json.JSONDecodeError as error:
        return build_parse_failure(
            body_text=body_text,
            content_type=content_type,
            error=error,
            max_preview_chars=max_preview_chars,
        )


def build_parse_failure(
    *,
    body_text: str,
    content_type: str | None,
    error: json.JSONDecodeError,
    max_preview_chars: int,
) -> dict[str, Any]:
    """
    Build a structured parse-failure payload for diagnostics.
    """

    return {
        "_parse_error": {
            "message": "Response body could not be parsed as JSON.",
            "content_type": content_type,
            "error_type": type(error).__name__,
            "error_message": error.msg,
            "line": error.lineno,
            "column": error.colno,
            "position": error.pos,
            "body_length": len(body_text),
            "body_preview": preview_text(
                body_text,
                max_chars=max_preview_chars,
            ),
        }
    }


def preview_text(text: str, *, max_chars: int) -> str:
    """
    Return a bounded preview of text so errors do not dump huge responses.
    """

    if len(text) <= max_chars:
        return text

    return text[:max_chars] + f"... <truncated; total chars={len(text)}>"