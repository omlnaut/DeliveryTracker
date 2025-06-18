import logging

import requests

from shared.Reddit.RedditCredentials import RedditCredentials
from shared.Reddit.RedditPost import RedditPost


class RedditClient:
    POST_BASE_URL = "https://oauth.reddit.com/r/{subreddit}/new.json?limit=100"
    AUTH_URL = "https://www.reddit.com/api/v1/access_token"

    def __init__(self, credentials: RedditCredentials):
        self.credentials = credentials
        self.access_token: str | None = None

    def _fetch_access_token(self) -> dict[str, str]:
        """Get access token for Reddit API using client credentials."""
        logging.info("Fetching Reddit access token")
        url = self.AUTH_URL
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

    def _get_access_token(self) -> str:
        if not self.access_token:
            logging.info("Access token not set, fetching new one")
            self.access_token = self._fetch_access_token()["access_token"]
        return self.access_token

    def get_posts(self, subreddit: str) -> list[RedditPost]:
        """Fetch posts from a subreddit."""
        logging.info(f"Fetching posts from subreddit: {subreddit}")
        url = self.build_subreddit_url(subreddit)
        raw_posts = self._get_raw_post_response(url)
        posts_data = raw_posts.get("data", {}).get("children", [])
        return [
            RedditPost(
                subreddit=subreddit,
                created_at_timestamp=post["data"]["created_utc"],
                title=post["data"]["title"],
                flair=post["data"].get("link_flair_text"),
                destination_url=post["data"].get("url", None),
            )
            for post in posts_data
        ]

    def build_subreddit_url(self, subreddit) -> str:
        url = self.POST_BASE_URL.format(subreddit=subreddit)
        return url

    def _get_raw_post_response(self, url: str) -> dict:
        """Get raw post response from Reddit."""
        headers = {
            "Authorization": f"Bearer {self._get_access_token()}",
            "User-Agent": self.credentials.user_agent,
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
