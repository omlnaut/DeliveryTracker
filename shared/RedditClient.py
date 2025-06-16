from dataclasses import dataclass
import logging

import requests


@dataclass
class RedditCredentials:
    client_id: str
    client_secret: str
    username: str
    password: str

    @property
    def user_agent(self) -> str:
        return f"script:deliverytracker:v1.0 (by /u/{self.username})"


class RedditClient:
    def __init__(self, credentials: RedditCredentials):
        self.credentials = credentials
        self.access_token: str | None = None

    def _fetch_access_token(self) -> str:
        """Get access token for Reddit API using client credentials."""
        logging.info("Fetching Reddit access token")
        url = "https://www.reddit.com/api/v1/access_token"
        headers = {
            "User-Agent": self.credentials.user_agent,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "password",
            "username": self.credentials.username,
            "password": self.credentials.password,
        }
        response = requests.post(
            url,
            headers=headers,
            data=data,
            auth=(self.credentials.client_id, self.credentials.client_secret),
        )
        response.raise_for_status()
        token_data = response.json()
        return token_data

    def get_access_token(self) -> str:
        if not self.access_token:
            logging.info("Access token not set, fetching new one")
            self.access_token = self._fetch_access_token()
        return self.access_token
