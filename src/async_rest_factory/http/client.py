from __future__ import annotations

from typing import Any, Mapping

import aiohttp

from async_rest_utils.exceptions import HttpResponseError
from async_rest_utils.http.parsing import parse_response_body


async def send_request(
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
    json_body: Mapping[str, Any] | list[Any] | None = None,
    headers: Mapping[str, str] | None = None,
) -> Any:
    """
    Send an HTTP request and return the parsed response body.

    Raises:
        HttpResponseError: When the response has an unsuccessful HTTP status.
    """

    async with session.request(
        method=method,
        url=url,
        params=dict(params) if params else None,
        json=json_body,
        headers=dict(headers) if headers else None,
    ) as response:
        body_text = await response.text()

        body = parse_response_body(
            body_text,
            content_type=response.headers.get("Content-Type"),
        )

        try:
            response.raise_for_status()
        except aiohttp.ClientResponseError as error:
            raise HttpResponseError(
                message="HTTP request failed",
                status=error.status,
                reason=error.message,
                url=str(error.request_info.real_url),
                body=body,
            ) from error

        return body