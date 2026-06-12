from __future__ import annotations

from typing import Any


class HttpResponseError(Exception):
    """HTTP request failure containing structured response details."""

    def __init__(
        self,
        message: str,
        status: int,
        reason: str,
        url: str,
        body: Any,
    ) -> None:
        super().__init__(message)

        self.status = status
        self.reason = reason
        self.url = url
        self.body = body