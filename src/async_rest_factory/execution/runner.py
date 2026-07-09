from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from typing import Any

import aiohttp

from async_rest_factory.auth import AuthContext, AuthFn
from async_rest_factory.execution.types import ConfigRunResult, FetchFn, RateLimiter
from async_rest_factory.patching import Cfg


async def run_configs(
    *,
    configs: Sequence[Cfg],
    fetch_fn: FetchFn,
    auth_fn: AuthFn | None = None,
    timeout_kwargs: Mapping[str, Any] | None = None,
    rate_limiter: RateLimiter | None = None,
    in_progress_limit: int = 1,
) -> list[ConfigRunResult]:
    """
    Execute REST configs using a stable aiohttp session and an API-specific
    fetch function.

    The runner owns generic execution concerns:
        - auth handoff
        - aiohttp session setup
        - timeout setup
        - concurrency limiting
        - optional config patching
        - optional rate limiting handoff

    The fetch_fn owns API-specific behavior:
        - pagination
        - response shape
        - next-page handling
        - record extraction
        - writing/sinking behavior
    """
    if in_progress_limit <= 0:
        raise ValueError("in_progress_limit must be greater than 0.")

    timeout = aiohttp.ClientTimeout(**dict(timeout_kwargs or {}))

    auth_context = await auth_fn() if auth_fn else AuthContext.no_auth()

    async with aiohttp.ClientSession(
        timeout=timeout,
        **auth_context.session_kwargs,
    ) as session:
        semaphore = asyncio.Semaphore(in_progress_limit)

        async def run_one(cfg: Cfg) -> ConfigRunResult:
            async with semaphore:
                patched_cfg = (
                    auth_context.cfg_patcher(cfg)
                    if auth_context.cfg_patcher
                    else cfg
                )

                return await fetch_fn(
                    session,
                    patched_cfg,
                    rate_limiter,
                )

        tasks = [
            asyncio.create_task(run_one(cfg))
            for cfg in configs
        ]

        return await asyncio.gather(*tasks)