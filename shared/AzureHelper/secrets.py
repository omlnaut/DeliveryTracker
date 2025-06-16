from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


def get_secret(secret_name: str) -> str:
    key_vault_url = "https://omlnaut-vaultier.vault.azure.net/"

    # Create a secret client using the DefaultAzureCredential
    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=key_vault_url, credential=credential)

    secret_str = secret_client.get_secret(secret_name).value

    if not secret_str:
        raise Exception(f"Secret {secret_name} not found in Key Vault")

    return secret_str
