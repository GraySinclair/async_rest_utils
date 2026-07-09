# async_rest_factory/exceptions.py

from __future__ import annotations

import json
from typing import Any


class HttpResponseError(Exception):
    """HTTP request failure containing structured response details."""

    def __init__(
        self,
        message: str,
        *,
        status: int,
        reason: str,
        url: str,
        body: Any = None,
    ) -> None:
        super().__init__(message)

        self.message = message
        self.status = status
        self.reason = reason
        self.url = url
        self.body = body

    def to_dict(self) -> dict[str, Any]:
        """Return structured error details for logging/debugging."""
        return {
            "message": self.message,
            "status": self.status,
            "reason": self.reason,
            "url": self.url,
            "body": self.body,
        }

    def __str__(self) -> str:
        """Return a readable structured representation of the error."""
        return json.dumps(
            self.to_dict(),
            indent=2,
            default=str,
        )