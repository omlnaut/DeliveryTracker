import json

from shared.AzureHelper.secrets import get_secret
from shared.Reddit import RedditCredentials


def load_reddit_credentials() -> RedditCredentials:
    secret_str = get_secret("RedditTrackerApp")

    if not secret_str:
        raise Exception("RedditCredentials secret not found in Key Vault")

    raw_credentials = json.loads(secret_str)

    return RedditCredentials(
        client_id=raw_credentials["client_id"],
        client_secret=raw_credentials["client_secret"],
        username=raw_credentials["username"],
        password=raw_credentials["password"],
    )
