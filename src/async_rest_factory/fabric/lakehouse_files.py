# async_rest_utils/fabric/lakehouse_files.py

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any
from uuid import uuid4


DEFAULT_LAKEHOUSE_FILES_ROOT = "/lakehouse/default/Files"


def write_rows_to_lakehouse_json(
    rows: Sequence[Mapping[str, Any]],
    source_system: str,
    table_name: str,
    *,
    lakehouse_files_root: str = DEFAULT_LAKEHOUSE_FILES_ROOT,
) -> str | None:
    """
    Write API response rows to a Fabric Lakehouse Files folder.

    The content is newline-delimited JSON, but the file uses a `.json`
    extension so the Fabric UI recognizes it as JSON in right-click
    "Load data" workflows.

    Default output path:

        /lakehouse/default/Files/{source_system}/{table_name}/data/{uuid}.json

    This path is intentional for pure Python Fabric notebooks because it
    writes to persistent Lakehouse storage instead of temporary notebook
    storage.
    """
    if not rows:
        return None

    import notebookutils

    root = lakehouse_files_root.rstrip("/")
    dir_path = f"{root}/{source_system}/{table_name}/data"

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