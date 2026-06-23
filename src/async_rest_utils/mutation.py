from typing import Any

def inject_cfg_value(cfg: dict, path: list[str | int], val: Any) -> dict:
    if not path:
        raise ValueError("path cannot be empty.")

    cur = cfg # traverse nested structure without losing the root reference

    for part in path[:-1]:
        cur = cur[part]

    cur[path[-1]] = val

    return cfg
