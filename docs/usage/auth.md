# Auth Usage

The `auth` package provides a structured way to pass API-specific authentication details into the generic request runner.

It is designed so API-specific auth logic stays outside the execution logic.

## Imports

```python
from async_rest_factory.auth import AuthContext, token_auth_context, token_header
```

For config patching used with auth:

```python
from async_rest_factory.patching import CfgPatch, patches_to_patcher
```

---

## AuthContext

`AuthContext` is the handoff object returned by an API-specific auth function.

It can contain:

- `session_kwargs`: values passed into `aiohttp.ClientSession`
- `cfg_patcher`: optional function that modifies a config before execution

```python
from async_rest_factory.auth import AuthContext
```

---

## No auth

Use `AuthContext.no_auth()` when an API does not require authentication.

```python
from async_rest_factory.auth import AuthContext


async def get_auth_context() -> AuthContext:
    return AuthContext.no_auth()
```

---

## Header auth

Use `AuthContext.with_headers()` when you already have the full headers dictionary.

```python
from async_rest_factory.auth import AuthContext


async def get_auth_context() -> AuthContext:
    return AuthContext.with_headers({
        "Authorization": "Bearer abc123",
        "Accept": "application/json",
    })
```

---

## Token header helper

Use `token_header()` when you want to build a token-style header dictionary.

```python
from async_rest_factory.auth import token_header


headers = token_header(
    header_name="Authorization",
    token="abc123",
    prefix="Bearer",
)
```

Result:

```python
{
    "Authorization": "Bearer abc123",
    "Accept": "application/json",
}
```

### Token without prefix

Useful for APIs that expect the raw token value.

```python
headers = token_header(
    header_name="X-Halo-Api-Key",
    token="abc123",
)
```

Result:

```python
{
    "X-Halo-Api-Key": "abc123",
    "Accept": "application/json",
}
```

### Custom extra headers

```python
headers = token_header(
    header_name="Authorization",
    token="abc123",
    prefix="Bearer",
    extra_headers={
        "Custom-Header": "value",
    },
)
```

---

## Token auth context helper

Use `token_auth_context()` when you want to return an `AuthContext` directly.

```python
from async_rest_factory.auth import AuthContext, token_auth_context


async def get_auth_context() -> AuthContext:
    token = "abc123"

    return token_auth_context(
        header_name="Authorization",
        token=token,
        prefix="Bearer",
    )
```

This is equivalent to:

```python
from async_rest_factory.auth import AuthContext, token_header


async def get_auth_context() -> AuthContext:
    token = "abc123"

    return AuthContext.with_headers(
        token_header(
            header_name="Authorization",
            token=token,
            prefix="Bearer",
        )
    )
```

---

## Common auth examples

### Bearer token

```python
async def get_auth_context() -> AuthContext:
    token = get_token_somehow()

    return token_auth_context(
        header_name="Authorization",
        token=token,
        prefix="Bearer",
    )
```

Produces:

```python
{
    "Authorization": "Bearer <token>",
    "Accept": "application/json",
}
```

### Token prefix

```python
async def get_auth_context() -> AuthContext:
    token = get_token_somehow()

    return token_auth_context(
        header_name="Authorization",
        token=token,
        prefix="Token",
    )
```

Produces:

```python
{
    "Authorization": "Token <token>",
    "Accept": "application/json",
}
```

### API key header

```python
async def get_auth_context() -> AuthContext:
    api_key = get_key_somehow()

    return token_auth_context(
        header_name="X-Halo-Api-Key",
        token=api_key,
    )
```

Produces:

```python
{
    "X-Halo-Api-Key": "<api_key>",
    "Accept": "application/json",
}
```

---

## Cookie auth

Use `AuthContext.with_cookies()` when an API requires cookies instead of headers.

```python
from async_rest_factory.auth import AuthContext


async def get_auth_context() -> AuthContext:
    return AuthContext.with_cookies({
        "session_id": "abc123",
    })
```

---

## Custom session kwargs

Use `AuthContext.with_session_kwargs()` when the API requires custom `aiohttp.ClientSession` options.

```python
from async_rest_factory.auth import AuthContext


async def get_auth_context() -> AuthContext:
    return AuthContext.with_session_kwargs(
        headers={
            "Authorization": "Bearer abc123",
            "Accept": "application/json",
        },
        cookies={
            "session_id": "cookie-value",
        },
    )
```

---

## Auth with runtime config patching

Some APIs need request-specific values inserted into the request config at runtime.

For example, a watermark may be stored separately from the request body template, then inserted before execution.

```python
from async_rest_factory.auth import AuthContext, token_auth_context
from async_rest_factory.patching import CfgPatch, patches_to_patcher


async def get_auth_context() -> AuthContext:
    token = get_token_somehow()
    watermark_value = "2026-06-18T14:37:52Z"

    auth_context = token_auth_context(
        header_name="Authorization",
        token=token,
        prefix="Bearer",
    )

    patcher = patches_to_patcher([
        CfgPatch(
            path=(
                "query_template",
                "request_body",
                "filters",
                0,
                "$gte",
                "audit.modifiedDateTime",
            ),
            value=watermark_value,
        )
    ])

    return AuthContext(
        session_kwargs=auth_context.session_kwargs,
        cfg_patcher=patcher,
    )
```

This keeps API-specific request mutation outside the generic runner.

---

## How the runner should consume AuthContext

A generic runner should treat `AuthContext` as a structured handoff.

```python
auth_context = await auth_fn()

if auth_context.cfg_patcher:
    cfg = auth_context.cfg_patcher(cfg)

async with aiohttp.ClientSession(**auth_context.session_kwargs) as session:
    result = await fetch_loop(session, cfg)
```

The runner does not need to know:

- how the token was created
- which header the API uses
- whether auth uses headers, cookies, or custom session kwargs
- which config fields are patched at runtime

It only receives:

```python
auth_context.session_kwargs
auth_context.cfg_patcher
```

---

## Recommended pattern

Each API integration should define its own auth function.

```python
from async_rest_factory.auth import AuthContext, token_auth_context
from async_rest_factory.fabric import get_key_vault_secret


async def get_hubspot_auth_context() -> AuthContext:
    token = get_key_vault_secret("hubspot-api-token")

    return token_auth_context(
        header_name="Authorization",
        token=token,
        prefix="Bearer",
    )
```

Then pass that function into the generic runner.

```python
await run_configs(
    configs=configs,
    auth_fn=get_hubspot_auth_context,
)
```

---

## Design rule

API-specific auth logic belongs in the integration layer.

Generic execution logic should only know how to consume `AuthContext`.