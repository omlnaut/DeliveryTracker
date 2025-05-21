from pathlib import Path
import sys
import json

from google.oauth2.credentials import Credentials


root_dir = Path("/workspaces/DeliveryTracker")


def add_workspace_to_path():
    root_dir = Path("/workspaces/DeliveryTracker")
    sys.path.insert(0, str(root_dir))


def load_google_credentials() -> Credentials:
    credentials_info = json.load(
        (root_dir / "google_token/logged_in_credentials.json").open()
    )
    credentials = Credentials.from_authorized_user_info(credentials_info)
    return credentials
