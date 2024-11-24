from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone
import os.path
import pickle

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class GmailService:
    def __init__(
        self, credentials_file="credentials.json", token_file="gmail_token.pickle"
    ):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.creds = None
        self.service = None

    def authenticate(self):
        """Authenticate with Gmail API."""
        if os.path.exists(self.token_file):
            with open(self.token_file, "rb") as token:
                self.creds = pickle.load(token)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                self.creds = flow.run_local_server(port=0)

            with open(self.token_file, "wb") as token:
                pickle.dump(self.creds, token)

        self.service = build("gmail", "v1", credentials=self.creds)

    def get_recent_emails(self, days=1):
        """
        Fetch emails received in the last specified hours.

        Args:
            hours (int): Number of hours to look back (default: 1)

        Returns:
            list: List of dictionaries containing email details
        """
        if not self.service:
            self.authenticate()

        # Calculate time threshold
        time_threshold = datetime.now(timezone.utc) - timedelta(days=days)
        query = f"after:{int(time_threshold.timestamp())}"

        try:
            results = (
                self.service.users().messages().list(userId="me", q=query).execute()
            )

            messages = results.get("messages", [])
            emails = []

            for message in messages:
                msg_details = (
                    self.service.users()
                    .messages()
                    .get(
                        userId="me",
                        id=message["id"],
                        format="metadata",
                        metadataHeaders=["From", "Subject", "Date"],
                    )
                    .execute()
                )

                headers = msg_details["payload"]["headers"]
                email_data = {
                    "id": message["id"],
                    "from": next(
                        (h["value"] for h in headers if h["name"] == "From"), ""
                    ),
                    "subject": next(
                        (h["value"] for h in headers if h["name"] == "Subject"), ""
                    ),
                    "date": next(
                        (h["value"] for h in headers if h["name"] == "Date"), ""
                    ),
                    "snippet": msg_details.get("snippet", ""),
                }
                emails.append(email_data)

            return emails

        except Exception as e:
            print(f"Error fetching emails: {str(e)}")
            return []


# Usage example:
if __name__ == "__main__":
    gmail = GmailService()
    recent_emails = gmail.get_recent_emails()
    for email in recent_emails:
        print(f"From: {email['from']}")
        print(f"Subject: {email['subject']}")
        print(f"Date: {email['date']}")
        print(f"Snippet: {email['snippet']}")
        print("-" * 50)
