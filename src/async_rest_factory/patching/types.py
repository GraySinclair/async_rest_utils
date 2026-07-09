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