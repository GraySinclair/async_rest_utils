# async-rest-factory

Reusable async REST ingestion utilities for Microsoft Fabric notebooks.

This package contains stable helper functions used across REST ingestion notebooks, including:

- async HTTP request execution with `aiohttp`
- structured HTTP error handling
- pagination helpers
- template utilities
- lakehouse file sink helpers
- watermark helpers
- config table merge helpers

The goal is to keep notebooks focused on orchestration and table-specific configuration, while moving stable reusable mechanics into a versioned Python package.

---

## Package name

The installable package name is:

```bash
async-rest-utils
