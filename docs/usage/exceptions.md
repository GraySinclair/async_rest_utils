# Exceptions Usage

The `exceptions` package contains custom exception types used by the request framework.

These exceptions are designed to carry structured diagnostic details, so callers do not need to manually print `vars(error)` or duplicate logging code.

## Imports

```python
from async_rest_factory.exceptions import HttpResponseError
```

---

## HttpResponseError

`HttpResponseError` represents an HTTP response failure.

It is used when a request reaches the server, receives a response, but the response status indicates failure.

Examples:

- `400 Bad Request`
- `401 Unauthorized`
- `403 Forbidden`
- `404 Not Found`
- `429 Too Many Requests`
- `500 Internal Server Error`

---

## Basic raise example

```python
from async_rest_factory.exceptions import HttpResponseError


raise HttpResponseError(
    "HTTP request failed",
    status=401,
    reason="Unauthorized",
    url="https://api.example.com/data",
    body={
        "error": "invalid_token",
        "message": "The provided token is expired.",
    },
)
```

When printed or raised uncaught, the exception displays structured JSON-style output.

Example output:

```text
HttpResponseError: {
  "message": "HTTP request failed",
  "status": 401,
  "reason": "Unauthorized",
  "url": "https://api.example.com/data",
  "body": {
    "error": "invalid_token",
    "message": "The provided token is expired."
  }
}
```

---

## Recommended class shape

```python
# async_rest_factory/exceptions/http.py

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
        """Return structured error details."""
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
```

---

## Package structure

Recommended structure:

```text
async_rest_factory/
    exceptions/
        __init__.py
        http.py
```

### `exceptions/__init__.py`

```python
# async_rest_factory/exceptions/__init__.py

from async_rest_factory.exceptions.http import HttpResponseError

__all__ = [
    "HttpResponseError",
]
```

This allows:

```python
from async_rest_factory.exceptions import HttpResponseError
```

instead of:

```python
from async_rest_factory.exceptions.http import HttpResponseError
```

---

## Usage inside the HTTP client

`HttpResponseError` is usually raised inside the request wrapper after reading the response body.

```python
import aiohttp

from async_rest_factory.exceptions import HttpResponseError
from async_rest_factory.http.parsing import parse_response_body


async def send_request(
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    *,
    params=None,
    json_body=None,
):
    async with session.request(
        method=method,
        url=url,
        params=params,
        json=json_body,
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

The important part is reading the body before calling `raise_for_status()`:

```python
body_text = await response.text()
```

That ensures the custom exception includes the API response body.

---

## Catching HttpResponseError

Because `HttpResponseError` represents itself, the caller usually does not need to print anything manually.

```python
from async_rest_factory.exceptions import HttpResponseError


try:
    result = await run_configs(configs)
except HttpResponseError:
    raise
```

In many cases, the `try` / `except` can be removed completely:

```python
result = await run_configs(configs)
```

If the exception is unhandled, Python will display the structured details.

---

## When to log explicitly

Use `to_dict()` when sending structured details to a logger, table, or monitoring system.

```python
try:
    result = await run_configs(configs)
except HttpResponseError as error:
    log_record = error.to_dict()

    # Example:
    # write_error_to_table(log_record)

    raise
```

Use `str(error)` when you want a formatted text version.

```python
try:
    result = await run_configs(configs)
except HttpResponseError as error:
    print(str(error))
    raise
```

Because `__str__()` is implemented, this also works:

```python
print(error)
```

---

## Avoid this pattern

Do not repeat this everywhere:

```python
import json

try:
    result = await run_configs(configs)
except HttpResponseError as error:
    print(json.dumps(vars(error), indent=2, default=str))
    raise
```

That formatting belongs inside the exception class.

Prefer:

```python
try:
    result = await run_configs(configs)
except HttpResponseError:
    raise
```

or:

```python
try:
    result = await run_configs(configs)
except HttpResponseError as error:
    log_record = error.to_dict()
    raise
```

---

## Parse failure body example

If a response body cannot be parsed as JSON, the HTTP parsing layer may return a structured parse error as the exception body.

Example body:

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

The resulting exception output still has the same top-level shape:

```python
{
    "message": "HTTP request failed",
    "status": 500,
    "reason": "Internal Server Error",
    "url": "https://api.example.com/data",
    "body": {
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
}
```

---

## Recommended design rule

Low-level modules should raise structured exceptions.

Higher-level runners should usually not format them manually.

```text
http/client.py
    raises HttpResponseError

runner.py
    lets HttpResponseError bubble up

notebook/script
    either lets the error display naturally
    or logs error.to_dict()
```

This keeps error formatting centralized and prevents repeated debug-print code across API integrations.