# Throttling Usage

The `throttling` subpackage contains helpers for controlling request pacing.

It is designed for APIs that enforce rate limits such as:

- requests per second
- requests per minute
- requests per hour
- shared quotas across concurrent tasks

The throttling layer should control **when** requests are allowed to start. The HTTP layer should still handle **how** a single request is sent.

---

## Imports

```python
from async_rest_factory.throttling import LeakyBucketRateLimiter
```

---

## Package structure

```text
async_rest_factory/
    throttling/
        __init__.py
        leaky_bucket.py
```

---

## `throttling/__init__.py`

```python
# async_rest_factory/throttling/__init__.py

from async_rest_factory.throttling.leaky_bucket import LeakyBucketRateLimiter

__all__ = [
    "LeakyBucketRateLimiter",
]
```

---

# LeakyBucketRateLimiter

`LeakyBucketRateLimiter` is an async rate limiter that enforces a minimum delay between request starts.

Example:

```python
from async_rest_factory.throttling import LeakyBucketRateLimiter


rate_limiter = LeakyBucketRateLimiter(requests_per_minute=100)
```

Then before each request:

```python
await rate_limiter.wait()
```

---

# Recommended `leaky_bucket.py`

```python
# async_rest_factory/throttling/leaky_bucket.py

from __future__ import annotations

import asyncio
import time


class LeakyBucketRateLimiter:
    """
    Async leaky-bucket-style rate limiter.

    Enforces a minimum delay between request starts.

    Example:
        limiter = LeakyBucketRateLimiter(requests_per_minute=100)

        await limiter.wait()
        response = await send_request(...)
    """

    def __init__(
        self,
        requests_per_minute: int,
        *,
        display_wait_time: bool = False,
    ) -> None:
        if requests_per_minute <= 0:
            raise ValueError("requests_per_minute must be greater than 0.")

        self.interval = 60 / requests_per_minute
        self.next_allowed_time = 0.0
        self.lock = asyncio.Lock()
        self.display_wait_time = display_wait_time

    async def wait(self) -> float:
        """
        Wait until the next request is allowed.

        Returns:
            Number of seconds waited.
        """
        async with self.lock:
            now = time.monotonic()
            wait_seconds = max(0.0, self.next_allowed_time - now)

            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)

            self.next_allowed_time = time.monotonic() + self.interval

            if self.display_wait_time:
                print(f"Rate limiter waited {wait_seconds:.3f} seconds")

            return wait_seconds
```

---

# Basic usage

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

---

# Use inside a pagination loop

Call `wait()` before each request.

```python
from async_rest_factory.http import send_request
from async_rest_factory.throttling import LeakyBucketRateLimiter


async def fetch_pages(session, url: str):
    rate_limiter = LeakyBucketRateLimiter(requests_per_minute=100)

    page = 1
    results = []

    while page <= 50:
        await rate_limiter.wait()

        body = await send_request(
            session=session,
            method="GET",
            url=url,
            params={
                "page": page,
                "limit": 100,
            },
        )

        rows = body.get("results", [])

        if not rows:
            break

        results.extend(rows)
        page += 1

    return results
```

---

# Create the limiter outside the loop

The limiter stores timing state:

```python
self.next_allowed_time
```

Because of that, create it outside the request loop.

Good:

```python
rate_limiter = LeakyBucketRateLimiter(requests_per_minute=100)

for cfg in configs:
    await rate_limiter.wait()
    await send_request(...)
```

Avoid:

```python
for cfg in configs:
    rate_limiter = LeakyBucketRateLimiter(requests_per_minute=100)
    await rate_limiter.wait()
    await send_request(...)
```

Creating a new limiter each time resets the timing state and defeats the purpose.

---

# Share one limiter across concurrent tasks

If multiple tasks hit the same API quota, share the same limiter.

```python
from async_rest_factory.throttling import LeakyBucketRateLimiter


rate_limiter = LeakyBucketRateLimiter(requests_per_minute=100)


async def run_cfg(session, cfg):
    await rate_limiter.wait()

    return await send_request(
        session=session,
        method=cfg["http_method"],
        url=cfg["endpoint"],
    )


tasks = [
    run_cfg(session, cfg)
    for cfg in configs
]

results = await asyncio.gather(*tasks)
```

The limiter uses an internal `asyncio.Lock`, so concurrent tasks wait in a controlled sequence.

---

# Use with a generic runner

A generic runner can accept an optional rate limiter.

```python
async def fetch_loop(
    session,
    cfg,
    *,
    rate_limiter=None,
):
    while True:
        if rate_limiter is not None:
            await rate_limiter.wait()

        body = await send_request(
            session=session,
            method=cfg["http_method"],
            url=cfg["endpoint"],
        )

        ...
```

Call it like this:

```python
rate_limiter = LeakyBucketRateLimiter(requests_per_minute=100)

result = await fetch_loop(
    session=session,
    cfg=cfg,
    rate_limiter=rate_limiter,
)
```

---

# Wait time reporting

Enable `display_wait_time` when debugging request pacing.

```python
rate_limiter = LeakyBucketRateLimiter(
    requests_per_minute=100,
    display_wait_time=True,
)
```

Example output:

```text
Rate limiter waited 0.600 seconds
```

The `wait()` method also returns the number of seconds waited.

```python
wait_seconds = await rate_limiter.wait()

print(wait_seconds)
```

---

# Requests per minute behavior

This limiter spaces request starts evenly.

For example:

```python
LeakyBucketRateLimiter(requests_per_minute=100)
```

calculates:

```python
interval = 60 / 100
```

Result:

```text
0.6 seconds between request starts
```

So requests are started at approximately:

```text
0.0s
0.6s
1.2s
1.8s
2.4s
...
```

---

# Response time behavior

This limiter controls when requests **start**.

It does not wait for a response before calculating the next allowed request time beyond the normal flow of your code.

Example:

```python
await rate_limiter.wait()
body = await send_request(...)
```

The request starts only after the limiter allows it.

If the response takes a long time, the next request may not need to wait because enough time has already passed.

Example:

```text
minimum interval: 0.6 seconds
response time:    2.0 seconds
next wait:         0.0 seconds
```

That is usually desirable. The API quota typically cares about request start rate, not how long responses take.

---

# One limiter per quota

Use one shared limiter for requests that count against the same quota.

Example:

```python
hubspot_limiter = LeakyBucketRateLimiter(requests_per_minute=100)
intacct_limiter = LeakyBucketRateLimiter(requests_per_minute=60)
```

Then pass the relevant limiter to each API run.

```python
await run_configs(
    configs=hubspot_configs,
    rate_limiter=hubspot_limiter,
)

await run_configs(
    configs=intacct_configs,
    rate_limiter=intacct_limiter,
)
```

Do not share one limiter across unrelated APIs unless you intentionally want one global cap.

---

# Validation

`requests_per_minute` must be greater than zero.

```python
LeakyBucketRateLimiter(requests_per_minute=0)
```

raises:

```python
ValueError
```

This prevents invalid intervals such as division by zero.

---

# Common patterns

## 100 requests per minute

```python
rate_limiter = LeakyBucketRateLimiter(requests_per_minute=100)
```

This allows one request start approximately every `0.6` seconds.

## 60 requests per minute

```python
rate_limiter = LeakyBucketRateLimiter(requests_per_minute=60)
```

This allows one request start approximately every `1.0` second.

## 30 requests per minute

```python
rate_limiter = LeakyBucketRateLimiter(requests_per_minute=30)
```

This allows one request start approximately every `2.0` seconds.

---

# Design boundary

The throttling package should only control request pacing.

It should not know:

- how requests are sent
- how responses are parsed
- how configs are loaded
- how auth tokens are fetched
- how rows are written
- how pagination is interpreted

Those belong elsewhere:

```text
http/        request sending and response parsing
auth/        auth handoff
fabric/      Fabric runtime helpers
patching/    runtime config mutation
runner.py    orchestration and pagination
```

---

# Recommended design rule

Create the rate limiter at the same level where the API quota is understood.

For example:

```python
rate_limiter = LeakyBucketRateLimiter(requests_per_minute=100)

await run_configs(
    configs=configs,
    auth_fn=get_auth_context,
    rate_limiter=rate_limiter,
)
```

The generic runner should only call:

```python
await rate_limiter.wait()
```

It should not need to know why the rate is `100` requests per minute.