from __future__ import annotations

import json
from typing import Any

import aiohttp

from async_rest_utils.exceptions import HttpResponseError


def parse_response_body(body_text: str) -> Any:
    """
    Parse an HTTP response body as JSON.

    Returns an empty dictionary for an empty body and the original string
    when the body is not valid JSON.
    """
    if not body_text:
        return {}

    try:
        return json.loads(body_text)
    except json.JSONDecodeError:
        return body_text


async def send_request(
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | list[Any] | None = None,
) -> Any:
    """
    Send an HTTP request and return the parsed response body.

    Raises:
        HttpResponseError: When the response has an unsuccessful HTTP status.
    """
    async with session.request(
        method=method,
        url=url,
        params=params,
        json=json_body,
    ) as response:
        body_text = await response.text()
        body = parse_response_body(body_text)

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