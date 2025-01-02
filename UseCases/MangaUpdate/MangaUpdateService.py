from dataclasses import dataclass
import requests
from shared.AzureHelper.secrets import get_secret
from datetime import datetime
from enum import Enum


class MangaPublisher(Enum):
    """Publisher id (called group_id on MangaUpdate API). Go to publisher page in browser and search for "group_id"."""

    FLAMECOMICS = 57949066600
    REAPERSCANS = 11782777312


@dataclass
class MangaUpdateManga:
    title: str
    url: str
    series_id: int
    publisher: MangaPublisher


@dataclass
class MangaChapter:
    chapter: str
    release_date: datetime
    title: str


mangas = [
    MangaUpdateManga(
        title="Omniscient Reader's Viewpoint",
        url="https://flamecomics.xyz/series/2",
        series_id=50369844984,
        publisher=MangaPublisher.FLAMECOMICS,
    )
]


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

    def get_latest_chapter(self, manga: MangaUpdateManga) -> MangaChapter:
        """Get the latest chapter for a manga from a specific publisher"""
        releases_endpoint = f"{self.api_url}/releases/search"

        payload = {
            "search": str(manga.series_id),
            "search_type": "series",
            "asc": "desc",  # Get newest first
            "group_id": manga.publisher.value,
            "include_metadata": False,
        }

        try:
            response = requests.post(
                releases_endpoint, json=payload, headers=self.get_auth_headers()
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("results") or not data["results"]:
                raise Exception(f"No chapters found for manga {manga.title}")

            latest = data["results"][0]["record"]
            return MangaChapter(
                chapter=latest["chapter"],
                release_date=datetime.strptime(latest["release_date"], "%Y-%m-%d"),
                title=latest["title"],
            )
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get latest chapter: {str(e)}")
        except (KeyError, ValueError) as e:
            raise Exception(f"Invalid response format: {str(e)}")
