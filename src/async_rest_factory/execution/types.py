from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

import aiohttp

from async_rest_factory.patching import Cfg


class RateLimiter(Protocol):
    async def wait(self) -> float:
        ...


@dataclass(frozen=True, slots=True)
class ConfigRunResult:
    """
    Result for one config execution.
    """

    cfg: Cfg
    table_name: str | None = None
    source_system: str | None = None
    records_written: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


FetchFn = Callable[
    [aiohttp.ClientSession, Cfg, RateLimiter | None],
    Awaitable[ConfigRunResult],
]
