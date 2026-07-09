# async-rest-factory

A small utility package for building reusable async REST extraction workflows.

The package is designed to keep API-specific logic separate from generic execution logic.

## Purpose

`async-rest-factory` provides reusable building blocks for:

- async HTTP requests with `aiohttp`
- structured HTTP error handling
- response body parsing diagnostics
- token/header auth handoff
- runtime config patching
- request throttling
- Microsoft Fabric notebook helpers

## Package areas

```text
async_rest_factory/
    auth/          # AuthContext and token header helpers
    exceptions/    # Structured custom exceptions
    fabric/        # Fabric notebook helpers
    http/          # send_request and response parsing
    patching/      # Runtime nested config patching
    throttling/    # Async request rate limiting
```

## Install

```bash
uv pip install async-rest-factory
```

For local development:

```bash
uv pip install -e .
```

## Basic usage

```python
import aiohttp

from async_rest_factory.auth import token_auth_context
from async_rest_factory.http import send_request
from async_rest_factory.throttling import LeakyBucketRateLimiter


auth_context = token_auth_context(
    header_name="Authorization",
    token="abc123",
    prefix="Bearer",
)

rate_limiter = LeakyBucketRateLimiter(requests_per_minute=100)

async with aiohttp.ClientSession(**auth_context.session_kwargs) as session:
    await rate_limiter.wait()

    body = await send_request(
        session=session,
        method="GET",
        url="https://api.example.com/items",
    )
```

## Runtime config patching

```python
from async_rest_factory.patching import CfgPatch, apply_patches


cfg = apply_patches(
    cfg,
    patches=[
        CfgPatch(
            path=(
                "query_template",
                "request_body",
                "filters",
                0,
                "$gte",
                "audit.modifiedDateTime",
            ),
            value="2026-06-18T14:37:52Z",
        )
    ],
)
```

## Fabric helpers

```python
from async_rest_factory.fabric import (
    get_key_vault_secret,
    load_rest_configs,
    write_rows_to_lakehouse_json,
)


token = get_key_vault_secret("hubspot-api-token")
configs = load_rest_configs("hubspot")

path = write_rows_to_lakehouse_json(
    rows=rows,
    source_system="hubspot",
    table_name="deals",
)
```

## Documentation

Usage docs are organized by package area:

```text
docs/usage/
    auth.md
    exceptions.md
    fabric.md
    http.md
    patching.md
    throttling.md
```

## Design rules

- API-specific logic belongs outside the generic runner.
- Auth functions should return `AuthContext`.
- Runtime request changes should use `patching`.
- HTTP request/error handling should go through `send_request`.
- Fabric-specific helpers should stay inside `fabric/`.
- Heavy or runtime-specific imports should happen inside functions.

## Development

Run tests:

```bash
uv run pytest
```

Build package:

```bash
uv build
```
