# Patching Usage

The `patching` subpackage provides helpers for modifying nested runtime configs before they are passed to the generic request runner.

It is designed for workflows where API request templates are stored separately from runtime values such as:

- watermarks
- page sizes
- request filters
- dynamic request headers
- runtime query parameters
- endpoint-specific body values

This keeps API-specific mutation logic separate from generic execution logic.

---

## Imports

```python
from async_rest_factory.patching import (
    Cfg,
    CfgPatch,
    CfgPatcher,
    PathPart,
    apply_patches,
    patches_to_patcher,
    set_nested_value,
)
```

---

## Package structure

```text
async_rest_factory/
    patching/
        __init__.py
        types.py
        nested.py
```

---

## `patching/__init__.py`

```python
# async_rest_factory/patching/__init__.py

from async_rest_factory.patching.nested import (
    apply_patches,
    patches_to_patcher,
    set_nested_value,
)
from async_rest_factory.patching.types import (
    Cfg,
    CfgPatch,
    CfgPatcher,
    PathPart,
)

__all__ = [
    "Cfg",
    "CfgPatch",
    "CfgPatcher",
    "PathPart",
    "set_nested_value",
    "apply_patches",
    "patches_to_patcher",
]
```

---

# Core concepts

## `Cfg`

A config dictionary.

```python
Cfg = dict[str, Any]
```

Example:

```python
cfg = {
    "source_system": "intacct",
    "table_name": "journal_entry_lines",
    "http_method": "POST",
    "query_template": {
        "request_body": {
            "object": "general-ledger/journal-entry-line",
            "filters": [
                {
                    "$gte": {
                        "audit.modifiedDateTime": None,
                    }
                }
            ],
            "size": 2000,
        }
    },
}
```

---

## `PathPart`

A single piece of a nested path.

```python
PathPart = str | int
```

Use:

- `str` for dictionary keys
- `int` for list indexes

Example path:

```python
(
    "query_template",
    "request_body",
    "filters",
    0,
    "$gte",
    "audit.modifiedDateTime",
)
```

This points to:

```python
cfg["query_template"]["request_body"]["filters"][0]["$gte"]["audit.modifiedDateTime"]
```

---

## `CfgPatch`

A declarative patch instruction.

```python
CfgPatch(
    path=("query_template", "request_body", "size"),
    value=2000,
)
```

It means:

```text
Set this nested config path to this value.
```

A `CfgPatch` is data. It does not apply itself.

---

## `CfgPatcher`

A callable that receives a config and returns a patched config.

```python
CfgPatcher = Callable[[Cfg], Cfg]
```

Example:

```python
def patch_cfg(cfg: Cfg) -> Cfg:
    return set_nested_value(
        cfg,
        path=("query_template", "request_body", "size"),
        value=2000,
    )
```

A `CfgPatcher` is executable logic.

---

# Recommended `types.py`

```python
# async_rest_factory/patching/types.py

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any


Cfg = dict[str, Any]
PathPart = str | int
CfgPatcher = Callable[[Cfg], Cfg]


@dataclass(frozen=True, slots=True)
class CfgPatch:
    """
    Declarative nested config update.
    """

    path: Sequence[PathPart]
    value: Any
```

---

# Recommended `nested.py`

```python
# async_rest_factory/patching/nested.py

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
            raise TypeError(f"Expected string key for dict traversal, got {part!r}.")

        if part not in container:
            raise KeyError(f"Missing config key: {part!r}")

        return container[part]

    if isinstance(container, list):
        if not isinstance(part, int):
            raise TypeError(f"Expected integer index for list traversal, got {part!r}.")

        return container[part]

    raise TypeError(
        f"Cannot traverse into object of type {type(container).__name__} "
        f"using path part {part!r}."
    )


def _set_path_part(container: Any, part: PathPart, value: Any) -> None:
    if isinstance(container, dict):
        if not isinstance(part, str):
            raise TypeError(f"Expected string key for dict assignment, got {part!r}.")

        if part not in container:
            raise KeyError(f"Missing config key: {part!r}")

        container[part] = value
        return

    if isinstance(container, list):
        if not isinstance(part, int):
            raise TypeError(f"Expected integer index for list assignment, got {part!r}.")

        container[part] = value
        return

    raise TypeError(
        f"Cannot assign into object of type {type(container).__name__} "
        f"using path part {part!r}."
    )
```

---

# Set one nested value

Use `set_nested_value()` when you need to update one field.

```python
from async_rest_factory.patching import set_nested_value


cfg = set_nested_value(
    cfg,
    path=("query_template", "request_body", "size"),
    value=2000,
)
```

This returns a patched copy by default.

---

# In-place patching

By default, `set_nested_value()` deep-copies the config before patching.

```python
patched_cfg = set_nested_value(
    cfg,
    path=("query_template", "request_body", "size"),
    value=2000,
)
```

The original `cfg` is not modified.

To mutate the original config intentionally:

```python
set_nested_value(
    cfg,
    path=("query_template", "request_body", "size"),
    value=2000,
    in_place=True,
)
```

Use `in_place=True` only when mutation is intentional.

---

# Patch a watermark value

Example config:

```python
cfg = {
    "query_template": {
        "request_body": {
            "filters": [
                {
                    "$gte": {
                        "audit.modifiedDateTime": None,
                    }
                }
            ]
        }
    }
}
```

Patch the watermark:

```python
from async_rest_factory.patching import set_nested_value


cfg = set_nested_value(
    cfg,
    path=(
        "query_template",
        "request_body",
        "filters",
        0,
        "$gte",
        "audit.modifiedDateTime",
    ),
    value="2026-06-18T14:37:52Z",
)
```

Result:

```python
{
    "query_template": {
        "request_body": {
            "filters": [
                {
                    "$gte": {
                        "audit.modifiedDateTime": "2026-06-18T14:37:52Z",
                    }
                }
            ]
        }
    }
}
```

---

# Apply multiple patches

Use `CfgPatch` and `apply_patches()` when multiple runtime values need to be inserted.

```python
from async_rest_factory.patching import CfgPatch, apply_patches


cfg = apply_patches(
    cfg,
    patches=[
        CfgPatch(
            path=("query_template", "request_body", "size"),
            value=2000,
        ),
        CfgPatch(
            path=(
                "query_template",
                "request_body",
                "filters",
                0,
                "$gte",
                "audit.modifiedDateTime",
            ),
            value="2026-06-18T14:37:52Z",
        ),
    ],
)
```

---

# Convert patches into a patcher

Use `patches_to_patcher()` when a generic runner expects a callable `CfgPatcher`.

```python
from async_rest_factory.patching import CfgPatch, patches_to_patcher


patcher = patches_to_patcher([
    CfgPatch(
        path=("query_template", "request_body", "size"),
        value=2000,
    ),
    CfgPatch(
        path=(
            "query_template",
            "request_body",
            "filters",
            0,
            "$gte",
            "audit.modifiedDateTime",
        ),
        value="2026-06-18T14:37:52Z",
    ),
])
```

Then apply it:

```python
cfg = patcher(cfg)
```

---

# Use patching with AuthContext

`AuthContext` can optionally carry a `cfg_patcher`.

This allows an API-specific auth function to return both:

- session kwargs for `aiohttp.ClientSession`
- config patching logic to apply before request execution

```python
from async_rest_factory.auth import AuthContext, token_auth_context
from async_rest_factory.patching import CfgPatch, patches_to_patcher


async def get_auth_context() -> AuthContext:
    token = "abc123"
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

---

# Runner usage

The runner does not need to know what the patcher changes.

```python
auth_context = await auth_fn()

if auth_context.cfg_patcher:
    cfg = auth_context.cfg_patcher(cfg)
```

That keeps the runner generic.

The runner only knows:

```text
If a cfg_patcher exists, apply it before sending requests.
```

It does not need to know:

- which API uses the watermark
- where the API expects filters
- whether the value goes in request body, params, or headers
- how the watermark value was calculated

---

# API-specific patch builder

A clean pattern is to create small API-specific functions that return patches.

```python
from async_rest_factory.patching import CfgPatch


def build_intacct_watermark_patches(watermark_value: str) -> list[CfgPatch]:
    return [
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
    ]
```

Then use it:

```python
from async_rest_factory.patching import patches_to_patcher


patches = build_intacct_watermark_patches(watermark_value)
patcher = patches_to_patcher(patches)
```

This keeps API-specific path knowledge outside the generic runner.

---

# Patch request parameters

Example config:

```python
cfg = {
    "query_template": {
        "request_parameters": {
            "page": 1,
            "page_size": 100,
        }
    }
}
```

Patch the page number:

```python
cfg = set_nested_value(
    cfg,
    path=("query_template", "request_parameters", "page"),
    value=2,
)
```

---

# Patch request body

Example config:

```python
cfg = {
    "query_template": {
        "request_body": {
            "limit": 100,
            "after": None,
        }
    }
}
```

Patch the cursor:

```python
cfg = set_nested_value(
    cfg,
    path=("query_template", "request_body", "after"),
    value="next-page-token",
)
```

---

# Patch request headers

Example config:

```python
cfg = {
    "query_template": {
        "request_headers": {
            "X-Custom-Header": None,
        }
    }
}
```

Patch the header:

```python
cfg = set_nested_value(
    cfg,
    path=("query_template", "request_headers", "X-Custom-Header"),
    value="runtime-value",
)
```

---

# Strict path behavior

The patching helpers are intentionally strict.

If a key is missing, this raises `KeyError`:

```python
cfg = set_nested_value(
    cfg,
    path=("query_template", "request_body", "missing_key"),
    value="abc",
)
```

If a list index is invalid, this raises `IndexError`:

```python
cfg = set_nested_value(
    cfg,
    path=("query_template", "request_body", "filters", 99),
    value="abc",
)
```

If the path uses the wrong type, this raises `TypeError`:

```python
cfg = set_nested_value(
    cfg,
    path=("query_template", "request_body", "filters", "0"),
    value="abc",
)
```

For a list, the path part must be an integer:

```python
0
```

not:

```python
"0"
```

---

# Why paths are strict

Strict paths catch bad config templates early.

For runtime request templates, a missing path usually means one of these is wrong:

- the config template changed
- the API-specific patch path is wrong
- the wrong patcher was applied to the wrong endpoint
- the stored config is malformed

Failing fast is better than silently creating invalid request bodies.

---

# Recommended design rule

Use patching for runtime values that are known only when the run starts.

Good examples:

```text
watermark values
pagination cursors
page numbers
dynamic filters
dynamic request params
runtime header values
```

Avoid using patching for static API config that should already live in the stored template.

Static values belong in the config table/template.

Runtime values belong in patching.

---

# Design boundary

The patching package should know how to update nested structures.

It should not know:

- where configs are loaded from
- which API is being called
- how HTTP requests are sent
- how auth tokens are fetched
- how rows are written

Those belong elsewhere:

```text
fabric/       loading configs, secrets, Lakehouse Files
auth/         auth context and token helpers
http/         request sending and response parsing
runner.py     orchestration
```

The dependency direction should stay simple:

```text
patching/types
    ↓
patching/nested
    ↓
auth/context may reference CfgPatcher
    ↓
runner applies cfg_patcher
```