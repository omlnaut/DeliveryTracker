import json
from google.oauth2.credentials import Credentials

from shared.AzureHelper.secrets import get_secret


def load_gcloud_credentials() -> Credentials:
    secret_str = get_secret("GcloudCredentials")

    if not secret_str:
        raise Exception("GcloudCredentials secret not found in Key Vault")

    credentials_info = json.loads(secret_str)
    return Credentials.from_authorized_user_info(credentials_info)
