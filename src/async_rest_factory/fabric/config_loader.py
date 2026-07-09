from __future__ import annotations

import json
from typing import Any


def load_rest_configs(source_system: str) -> list[dict[str, Any]]:
    """
    Load enabled REST configurations for a source system from the Ops Lakehouse.

    JSON strings in the query_template column are converted to Python
    dictionaries.
    """
    import notebookutils
    import pandas as pd

    collections_rest_calls_table_query = f"""
        SELECT *
        FROM Ops.collections.rest_calls
        WHERE source_system = '{source_system}'
          AND is_enabled = 'true'
    """

    conn = notebookutils.data.connect_to_item("Ops", item_type="Lakehouse")
    df = conn.query(collections_rest_calls_table_query)

    if df is None:
        raise LookupError(
            f"No REST configs returned for source_system={source_system!r}. "
            "conn.query() returned None."
        )

    configs = (
        df.astype(object)
        .where(pd.notna(df), None)
        .to_dict(orient="records")
    )

    for cfg in configs:
        query_template = cfg.get("query_template")

        if isinstance(query_template, str) and query_template.strip():
            cfg["query_template"] = json.loads(query_template)

    return configs
