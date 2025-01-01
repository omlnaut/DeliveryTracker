import requests
from shared.AzureHelper.secrets import get_secret


class MangaUpdateService:
    def __init__(self):
        self.api_url = "https://api.mangaupdates.com/v1"
        self.session_token = None
        self._load_and_login()

    def _load_and_login(self):
        """Load credentials from Azure Key Vault and perform login"""
        try:
            username = "omlnaut"
            password = get_secret("MangaUpdatePassword")
            self.login(username, password)
        except Exception as e:
            raise Exception(f"Failed to load credentials and login: {str(e)}")

    def login(self, username: str, password: str):
        """Perform login to MangaUpdate API and store session token"""
        login_endpoint = f"{self.api_url}/account/login"
        login_data = {"username": username, "password": password}

        try:
            response = requests.put(login_endpoint, json=login_data)
            response.raise_for_status()
            data = response.json()

            if "context" not in data or "session_token" not in data["context"]:
                raise Exception("Invalid response format: missing session token")

            self.session_token = data["context"]["session_token"]
        except requests.exceptions.RequestException as e:
            raise Exception(f"Login failed: {str(e)}")

    def get_auth_headers(self):
        """Get headers with authentication token"""
        if not self.session_token:
            raise Exception("Not logged in. Call login() first.")

        return {"Authorization": f"Bearer {self.session_token}"}
