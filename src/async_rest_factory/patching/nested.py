from __future__ import annotations

from collections.abc import Sequence
from copy import deepcopy
from typing import Any

from async_rest_factory.patching.types import Cfg, CfgPatch, CfgPatcher, PathPart


def set_nested_value(
    cfg: Cfg,
    path: Sequence[PathPart],
    value: Any,
    *,
    in_place: bool = False,
) -> Cfg:
    """
    Set a nested value inside a config dictionary.

    By default, returns a deep-copied config so the original config is not
    mutated. Use in_place=True to mutate directly.
    """
    if not path:
        raise ValueError("path cannot be empty.")

    updated = cfg if in_place else deepcopy(cfg)
    current: Any = updated

    for part in path[:-1]:
        current = _get_path_part(current, part)

    _set_path_part(current, path[-1], value)

    return updated


def apply_patches(
    cfg: Cfg,
    patches: Sequence[CfgPatch],
    *,
    in_place: bool = False,
) -> Cfg:
    """
    Apply multiple declarative config patches.
    """
    updated = cfg if in_place else deepcopy(cfg)

    for patch in patches:
        set_nested_value(
            updated,
            path=patch.path,
            value=patch.value,
            in_place=True,
        )

    return updated


def patches_to_patcher(
    patches: Sequence[CfgPatch],
) -> CfgPatcher:
    """
    Convert declarative patches into a callable config patcher.
    """

    def patcher(cfg: Cfg) -> Cfg:
        return apply_patches(cfg, patches)

    return patcher


def _get_path_part(container: Any, part: PathPart) -> Any:
    if isinstance(container, dict):
        if not isinstance(part, str):
            raise TypeError(
                f"Expected string key for dict traversal, got {part!r}."
            )

        if part not in container:
            raise KeyError(f"Missing config key: {part!r}")

        return container[part]

    if isinstance(container, list):
        if not isinstance(part, int):
            raise TypeError(
                f"Expected integer index for list traversal, got {part!r}."
            )

        return container[part]

    raise TypeError(
        f"Cannot traverse into object of type {type(container).__name__} "
        f"using path part {part!r}."
    )


def _set_path_part(container: Any, part: PathPart, value: Any) -> None:
    if isinstance(container, dict):
        if not isinstance(part, str):
            raise TypeError(
                f"Expected string key for dict assignment, got {part!r}."
            )

        if part not in container:
            raise KeyError(f"Missing config key: {part!r}")

        container[part] = value
        return

    if isinstance(container, list):
        if not isinstance(part, int):
            raise TypeError(
                f"Expected integer index for list assignment, got {part!r}."
            )

        container[part] = value
        return

    raise TypeError(
        f"Cannot assign into object of type {type(container).__name__} "
        f"using path part {part!r}."
    )
