from __future__ import annotations

import json
from typing import Any
from uuid import uuid4


def sink_rows_to_file(
    rows: list[dict[str, Any]],
    source_system: str,
    table_name: str,
) -> str | None:
    """
    Write API response rows to a Lakehouse Files folder as JSONL.

    Requires Microsoft Fabric notebook runtime with notebookutils available.

    Returns:
        The written file path, or None when rows is empty.
    """
    if not rows:
        return None

    import notebookutils

    dir_path = f"/lakehouse/default/Files/{source_system}/{table_name}/data"
    notebookutils.fs.mkdirs(dir_path)

    path = f"{dir_path}/{uuid4().hex}.json"
    records = "\n".join(
        json.dumps(row, ensure_ascii=False, default=str)
        for row in rows
    )

    successful_write = notebookutils.fs.put(
        file=path,
        content=records,
        overwrite=False,
    )

    if not successful_write:
        raise RuntimeError(f"Failed to write file: {path}")

    return path