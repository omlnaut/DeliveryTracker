import json
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from google.oauth2.credentials import Credentials


def get_secret(secret_name: str) -> str:
    key_vault_url = "https://omlnaut-vaultier.vault.azure.net/"

    # Create a secret client using the DefaultAzureCredential
    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=key_vault_url, credential=credential)

    secret_str = secret_client.get_secret(secret_name).value

    if not secret_str:
        raise Exception(f"Secret {secret_name} not found in Key Vault")

    return secret_str


def load_gcloud_credentials() -> Credentials:
    secret_str = get_secret("GcloudCredentials")

    if not secret_str:
        raise Exception("GcloudCredentials secret not found in Key Vault")

    credentials_info = json.loads(secret_str)
    return Credentials.from_authorized_user_info(credentials_info)
