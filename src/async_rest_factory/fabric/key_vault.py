from __future__ import annotations


DEFAULT_KEY_VAULT_URL = "https://andersfabric-kv.vault.azure.net/"


def get_key_vault_secret(
    secret_name: str,
    *,
    vault_url: str = DEFAULT_KEY_VAULT_URL,
) -> str:
    """
    Fetch a secret from Azure Key Vault using Microsoft Fabric credentials.

    Requires the Microsoft Fabric notebook runtime.
    """
    import notebookutils

    return notebookutils.credentials.getSecret(
        vault_url,
        secret_name,
    )