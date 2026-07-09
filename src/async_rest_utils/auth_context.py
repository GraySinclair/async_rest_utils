from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Mapping


Cfg = dict[str, Any]
CfgPatcher = Callable[[Cfg], Cfg]
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


def token_header(
    *,
    header_name: str,
    token: str,
    prefix: str | None = None,
    accept: str | None = "application/json",
    extra_headers: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """
    Builds a token-style header.

    Examples:
        token_header(header_name="Authorization", token="abc", prefix="Bearer")
        -> {"Authorization": "Bearer abc", "Accept": "application/json"}

        token_header(header_name="Authorization", token="abc", prefix="Token")
        -> {"Authorization": "Token abc", "Accept": "application/json"}

        token_header(header_name="X-Halo-Api-Key", token="abc")
        -> {"X-Api-Key": "abc", "Accept": "application/json"}
    """

    if prefix:
        value = f"{prefix.rstrip()} {token}"
    else:
        value = token

    headers = {
        header_name: value,
    }

    if accept:
        headers["Accept"] = accept

    if extra_headers:
        headers.update(dict(extra_headers))

    return headers


def token_auth_context(
    *,
    header_name: str,
    token: str,
    prefix: str | None = None,
    accept: str | None = "application/json",
    extra_headers: Mapping[str, str] | None = None,
) -> AuthContext:
    """
    Convenience wrapper that returns AuthContext directly.
    """

    return AuthContext.with_headers(
        token_header(
            header_name=header_name,
            token=token,
            prefix=prefix,
            accept=accept,
            extra_headers=extra_headers,
        )
    )
