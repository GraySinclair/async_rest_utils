# HTTP Usage

The `http` subpackage contains the generic async request wrapper and response parsing helpers.

It is designed to centralize:

- sending HTTP requests
- reading response bodies
- parsing JSON responses
- raising structured HTTP errors
- preserving failed response bodies for diagnostics

Generic execution logic should call `send_request()` instead of repeating request/error-handling code in each API integration.

---

## Imports

```python
from async_rest_factory.http import send_request, parse_response_body
```

For HTTP errors:

```python
from async_rest_factory.exceptions import HttpResponseError
```

---

## Package structure

```text
async_rest_factory/
    http/
        __init__.py
        client.py
        parsing.py

    exceptions/
        __init__.py
        http.py
```

---

## `http/__init__.py`

```python
# async_rest_factory/http/__init__.py

from async_rest_factory.http.client import send_request
from async_rest_factory.http.parsing import parse_response_body

__all__ = [
    "send_request",
    "parse_response_body",
]
```

This allows:

```python
from async_rest_factory.http import send_request
```

instead of:

```python
from async_rest_factory.http.client import send_request
```

---

# `send_request`

`send_request()` sends one HTTP request using an existing `aiohttp.ClientSession`.

It returns the parsed response body.

```python
from async_rest_factory.http import send_request
```

Basic usage:

```python
body = await send_request(
    session=session,
    method="GET",
    url="https://api.example.com/items",
)
```

With query parameters:

```python
body = await send_request(
    session=session,
    method="GET",
    url="https://api.example.com/items",
    params={
        "limit": 100,
        "page": 1,
    },
)
```

With a JSON request body:

```python
body = await send_request(
    session=session,
    method="POST",
    url="https://api.example.com/search",
    json_body={
        "filterGroups": [],
        "limit": 100,
    },
)
```

With request-level headers:

```python
body = await send_request(
    session=session,
    method="GET",
    url="https://api.example.com/items",
    headers={
        "Custom-Header": "value",
    },
)
```

---

# Recommended `client.py`

```python
# async_rest_factory/http/client.py

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import aiohttp

from async_rest_factory.exceptions import HttpResponseError
from async_rest_factory.http.parsing import parse_response_body


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
        HttpResponseError:
            When the response has an unsuccessful HTTP status.
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
                "HTTP request failed",
                status=error.status,
                reason=error.message,
                url=str(error.request_info.real_url),
                body=body,
            ) from error

        return body
```

---

# Important behavior

`send_request()` reads the response body before calling:

```python
response.raise_for_status()
```

This order matters.

Correct order:

```python
body_text = await response.text()
body = parse_response_body(body_text)

response.raise_for_status()
```

This ensures `HttpResponseError` can include the API response body when the request fails.

Avoid this order:

```python
response.raise_for_status()
body_text = await response.text()
```

If the response fails, the body may never be read.

---

# Response parsing

`parse_response_body()` converts response text into Python objects.

```python
from async_rest_factory.http import parse_response_body
```

Behavior:

| Response body | Return value |
|---|---|
| Empty body | `{}` |
| Valid JSON object | `dict` |
| Valid JSON array | `list` |
| Valid JSON scalar | parsed scalar |
| Invalid JSON | structured parse diagnostic |

---

# Recommended `parsing.py`

```python
# async_rest_factory/http/parsing.py

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
    """
    if not body_text:
        return {}

    try:
        return json.loads(body_text)

    except json.JSONDecodeError as error:
        return _build_parse_failure(
            body_text=body_text,
            content_type=content_type,
            error=error,
            max_preview_chars=max_preview_chars,
        )


def _build_parse_failure(
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
            "parser": "json",
            "content_type": content_type,
            "error_type": type(error).__name__,
            "error_message": error.msg,
            "line": error.lineno,
            "column": error.colno,
            "position": error.pos,
            "body_length": len(body_text),
            "body_preview": _preview_text(
                body_text,
                max_chars=max_preview_chars,
            ),
        }
    }


def _preview_text(text: str, *, max_chars: int) -> str:
    """
    Return a bounded preview of text so errors do not dump huge responses.
    """
    if len(text) <= max_chars:
        return text

    return text[:max_chars] + f"... <truncated; total chars={len(text)}>"
```

---

# Parse failure output

If the API returns HTML, plain text, or malformed JSON, the parser returns a structured diagnostic dictionary.

Example:

```python
{
    "_parse_error": {
        "message": "Response body could not be parsed as JSON.",
        "parser": "json",
        "content_type": "text/html; charset=utf-8",
        "error_type": "JSONDecodeError",
        "error_message": "Expecting value",
        "line": 1,
        "column": 1,
        "position": 0,
        "body_length": 8462,
        "body_preview": "<html>..."
    }
}
```

This makes failed responses easier to diagnose at a glance.

---

# Error handling

When a response has a failed HTTP status, `send_request()` raises `HttpResponseError`.

Example:

```python
from async_rest_factory.exceptions import HttpResponseError


try:
    body = await send_request(
        session=session,
        method="GET",
        url="https://api.example.com/items",
    )
except HttpResponseError:
    raise
```

Usually, no manual printing is needed because `HttpResponseError` represents itself.

---

## Example error output

```text
HttpResponseError: {
  "message": "HTTP request failed",
  "status": 401,
  "reason": "Unauthorized",
  "url": "https://api.example.com/items",
  "body": {
    "error": "invalid_token",
    "message": "The provided token is expired."
  }
}
```

---

# Logging structured errors

Use `to_dict()` when writing errors to logs, monitoring tables, or files.

```python
try:
    body = await send_request(
        session=session,
        method="GET",
        url="https://api.example.com/items",
    )
except HttpResponseError as error:
    error_record = error.to_dict()

    # Example:
    # write_error_to_table(error_record)

    raise
```

Avoid repeating this everywhere:

```python
import json

print(json.dumps(vars(error), indent=2, default=str))
```

That formatting belongs inside the exception class.

---

# Session reuse

`send_request()` expects a reusable `aiohttp.ClientSession`.

Good:

```python
import aiohttp

from async_rest_factory.http import send_request


async with aiohttp.ClientSession() as session:
    body_1 = await send_request(
        session=session,
        method="GET",
        url="https://api.example.com/items",
    )

    body_2 = await send_request(
        session=session,
        method="GET",
        url="https://api.example.com/users",
    )
```

Avoid creating a new session for every request:

```python
# Avoid this pattern.

async with aiohttp.ClientSession() as session:
    body_1 = await send_request(...)

async with aiohttp.ClientSession() as session:
    body_2 = await send_request(...)
```

A shared session is more efficient and keeps auth/session configuration centralized.

---

# Usage with AuthContext

`AuthContext.session_kwargs` can be passed directly into `aiohttp.ClientSession`.

```python
import aiohttp

from async_rest_factory.auth import token_auth_context
from async_rest_factory.http import send_request


auth_context = token_auth_context(
    header_name="Authorization",
    token="abc123",
    prefix="Bearer",
)

async with aiohttp.ClientSession(**auth_context.session_kwargs) as session:
    body = await send_request(
        session=session,
        method="GET",
        url="https://api.example.com/items",
    )
```

This keeps auth setup separate from request execution.

---

# Usage with runtime config templates

Example config shape:

```python
cfg = {
    "endpoint": "https://api.example.com/search",
    "http_method": "POST",
    "query_template": {
        "request_parameters": {
            "limit": 100,
        },
        "request_body": {
            "filters": [],
        },
    },
}
```

Sending a request from the config:

```python
query_template = cfg.get("query_template") or {}

body = await send_request(
    session=session,
    method=cfg["http_method"],
    url=cfg["endpoint"],
    params=query_template.get("request_parameters"),
    json_body=query_template.get("request_body"),
)
```

The HTTP layer does not need to know what API produced the config. It only sends the request.

---

# Usage with throttling

Use a rate limiter before calling `send_request()`.

```python
from async_rest_factory.http import send_request
from async_rest_factory.throttling import LeakyBucketRateLimiter


rate_limiter = LeakyBucketRateLimiter(requests_per_minute=100)

await rate_limiter.wait()

body = await send_request(
    session=session,
    method="GET",
    url="https://api.example.com/items",
)
```

For pagination loops, call the limiter before each request.

---

# GET request example

```python
body = await send_request(
    session=session,
    method="GET",
    url="https://api.example.com/items",
    params={
        "limit": 100,
        "page": 1,
    },
)
```

---

# POST request example

```python
body = await send_request(
    session=session,
    method="POST",
    url="https://api.example.com/search",
    json_body={
        "limit": 100,
        "filters": [],
    },
)
```

---

# DELETE request example

```python
body = await send_request(
    session=session,
    method="DELETE",
    url="https://api.example.com/items/123",
)
```

If the API returns an empty response body, `body` will be:

```python
{}
```

---

# Design rule

The `http` subpackage should know how to send one request and parse one response.

It should not know:

- how configs are loaded
- how secrets are fetched
- how rows are written to Fabric
- how pagination works
- which API-specific watermark should be injected

Those belong elsewhere:

```text
auth/         authentication handoff
fabric/       Fabric runtime helpers
patching/     runtime config mutation
throttling/   rate limiting
runner.py     orchestration and pagination
```

The dependency direction should stay simple:

```text
exceptions
    ↓
http/parsing
    ↓
http/client
    ↓
runner
    ↓
API-specific scripts/notebooks
```