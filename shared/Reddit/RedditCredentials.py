from dataclasses import dataclass


@dataclass
class RedditCredentials:
    client_id: str
    client_secret: str
    username: str
    password: str

    @property
    def user_agent(self) -> str:
        return f"script:deliverytracker:v1.0 (by /u/{self.username})"
