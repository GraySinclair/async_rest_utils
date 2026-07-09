from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from async_rest_factory.patching import CfgPatcher


AuthFn = Callable[[], Awaitable["AuthContext"]]


@dataclass(frozen=True, slots=True)
class AuthContext:
    """
    Structured handoff from an API-specific auth function to the generic runner.
    """

    session_kwargs: dict[str, Any] = field(default_factory=dict)
    cfg_patcher: CfgPatcher | None = None

    @classmethod
    def no_auth(cls) -> "AuthContext":
        return cls()

    @classmethod
    def with_headers(cls, headers: Mapping[str, str]) -> "AuthContext":
        return cls(session_kwargs={"headers": dict(headers)})

    @classmethod
    def with_cookies(cls, cookies: Mapping[str, str]) -> "AuthContext":
        return cls(session_kwargs={"cookies": dict(cookies)})

    @classmethod
    def with_session_kwargs(cls, **kwargs: Any) -> "AuthContext":
        return cls(session_kwargs=dict(kwargs))