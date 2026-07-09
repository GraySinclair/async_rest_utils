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


# USAGE:
# from async_rest_factory.throttling import LeakyBucketRateLimiter


# limiter = LeakyBucketRateLimiter(
#     requests_per_minute=100,
#     display_wait_time=True,
# )
