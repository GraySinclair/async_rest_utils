from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from typing import Any

import aiohttp

from async_rest_factory.auth import AuthContext, AuthFn
from async_rest_factory.execution.types import ConfigRunResult, FetchFn, RateLimiter
from async_rest_factory.patching import Cfg, CfgPatcher


async def run_configs(
    *,
    configs: Sequence[Cfg],
    fetch_fn: FetchFn,
    auth_fn: AuthFn | None = None,
    cfg_patcher: CfgPatcher | None = None,
    timeout_kwargs: Mapping[str, Any] | None = None,
    rate_limiter: RateLimiter | None = None,
    in_progress_limit: int = 1,
) -> list[ConfigRunResult]:
    """
    Execute REST configs using a stable aiohttp session and an API-specific
    fetch function.

    Responsibilities:

    run_configs:
        - create auth context
        - create aiohttp timeout/session
        - apply optional runtime config patcher
        - apply optional auth config patcher
        - execute configs in controlled batches
        - pass session/config/rate limiter to fetch_fn

    auth_fn:
        - handles authentication
        - may return AuthContext.cfg_patcher only when auth requires config
          modification

    cfg_patcher:
        - handles non-auth runtime config modification, such as watermark
          injection

    fetch_fn:
        - handles API-specific pagination, record extraction, and writing

    in_progress_limit:
        - controls batch size
        - each batch runs concurrently
        - the next batch does not start until the current batch finishes
    """
    if in_progress_limit <= 0:
        raise ValueError("in_progress_limit must be greater than 0.")

    timeout = aiohttp.ClientTimeout(**dict(timeout_kwargs or {}))
    auth_context = await auth_fn() if auth_fn else AuthContext.no_auth()

    results: list[ConfigRunResult] = []

    async with aiohttp.ClientSession(
        timeout=timeout,
        **auth_context.session_kwargs,
    ) as session:

        async def run_one(cfg: Cfg) -> ConfigRunResult:
            patched_cfg = cfg

            # Runtime/non-auth patching first.
            # Example: watermark injection.
            if cfg_patcher is not None:
                patched_cfg = cfg_patcher(patched_cfg)

            # Auth-specific patching second.
            # Example: token must be injected into request body/params.
            if auth_context.cfg_patcher is not None:
                patched_cfg = auth_context.cfg_patcher(patched_cfg)

            return await fetch_fn(
                session,
                patched_cfg,
                rate_limiter,
            )

        for i in range(0, len(configs), in_progress_limit):
            batch = configs[i : i + in_progress_limit]

            batch_results = await asyncio.gather(
                *(run_one(cfg) for cfg in batch)
            )

            results.extend(batch_results)

    return results
