from __future__ import annotations

from collections.abc import Mapping

from async_rest_factory.auth.context import AuthContext
from async_rest_factory.patching import CfgPatcher


def token_header(
    *,
    header_name: str,
    token: str,
    prefix: str | None = None,
    accept: str | None = "application/json",
    extra_headers: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """
    Build a token-style HTTP header.

    Examples:
        token_header(
            header_name="Authorization",
            token="abc",
            prefix="Bearer",
        )
        -> {"Authorization": "Bearer abc", "Accept": "application/json"}

        token_header(
            header_name="X-Halo-Api-Key",
            token="abc",
        )
        -> {"X-Halo-Api-Key": "abc", "Accept": "application/json"}
    """
    value = f"{prefix.rstrip()} {token}" if prefix else token

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
    cfg_patcher: CfgPatcher | None = None,
) -> AuthContext:
    """
    Build an AuthContext using a token-style HTTP header.

    cfg_patcher should only be supplied when the auth flow itself requires
    modifying request configs.
    """
    return AuthContext.with_headers(
        token_header(
            header_name=header_name,
            token=token,
            prefix=prefix,
            accept=accept,
            extra_headers=extra_headers,
        ),
        cfg_patcher=cfg_patcher,
    )
