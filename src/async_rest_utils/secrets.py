from __future__ import annotations

def fetch_secret(secret_name: str, *, vault_url: str = "https://andersfabric-kv.vault.azure.net/") -> str:
    """
    Fetch a secret from Azure Key Vault using Microsoft Fabric credentials.

    Requires the Microsoft Fabric notebook runtime.
    """
    import notebookutils

    return notebookutils.credentials.getSecret(
        vault_url,
        secret_name,
    )