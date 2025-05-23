"""Gmail service implementation for interacting with Gmail API."""

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from datetime import datetime, timedelta, timezone
import base64
import re
from bs4 import BeautifulSoup
from io import BytesIO
from typing import List

from shared.AzureHelper.download import get_temp_dir
from ..GmailQueryBuilder import GmailQueryBuilder
from .models import MessageId, AttachmentData, MemoryAttachment, GERMAN_MONTHS


class GmailService:
    def __init__(self, credentials: Credentials):
        self.credentials = credentials
        self.service = None

    def authenticate(self):
        """Authenticate with Gmail API."""
        # TODO figure out the type of the service
        self.service = build(
            "gmail", "v1", credentials=self.credentials, cache_discovery=False
        )

    def _query_messages_ids(self, query) -> list[MessageId]:
        """
        Query messages using Gmail API with the given query.

        Args:
            query (str): Gmail search query

        Returns:
            list: List of message IDs and thread IDs
        """
        if not self.service:
            self.authenticate()

        try:
            results = (
                self.service.users().messages().list(userId="me", q=query).execute()  # type: ignore
            )
            messages = results.get("messages", [])
            return [
                MessageId(id=message["id"], thread_id=message.get("threadId", ""))
                for message in messages
            ]
        except Exception as e:
            print(f"Error querying messages: {str(e)}")
            return []

    def _fetch_message_details(
        self, message_id: str, format="full", metadata_headers=None
    ):
        """
        Fetch details for a specific message.

        Args:
            message_id (str): The ID of the message to fetch
            format (str): The format to return the message in (full, metadata, minimal)
            metadata_headers (list): List of headers to include when format is metadata

        Returns:
            dict: Message details
        """
        try:
            kwargs = {"userId": "me", "id": message_id, "format": format}
            if metadata_headers and format == "metadata":
                kwargs["metadataHeaders"] = metadata_headers

            return self.service.users().messages().get(**kwargs).execute()  # type: ignore
        except Exception as e:
            print(f"Error fetching message details: {str(e)}")
            return None

    def _get_pdf_attachments(self, message_id) -> List[AttachmentData]:
        """
        Helper method to get PDF attachments from a message.

        Args:
            message_id (str): The ID of the message to get attachments from

        Returns:
            List[AttachmentData]: List of AttachmentData named tuples with filename and data
        """
        if not self.service:
            self.authenticate()

        try:
            message = self._fetch_message_details(message_id)
            if not message:
                return []

            attachments = []
            parts = message.get("payload", {}).get("parts", [])

            for part in parts:
                filename: str = part.get("filename", "")
                if filename.lower().endswith(".pdf"):
                    if "body" in part and "attachmentId" in part["body"]:
                        attachment = (
                            self.service.users()  # type: ignore
                            .messages()
                            .attachments()
                            .get(
                                userId="me",
                                messageId=message_id,
                                id=part["body"]["attachmentId"],
                            )
                            .execute()
                        )

                        if attachment:
                            attachment_data = base64.urlsafe_b64decode(
                                attachment["data"]
                            )
                            attachments.append(
                                AttachmentData(filename=filename, data=attachment_data)
                            )

            return attachments
        except Exception as e:
            print(f"Error fetching PDF attachments: {str(e)}")
            return []

    def download_pdf_attachments(self, message_id) -> list[str]:
        """
        Download all PDF attachments from a given message.

        Args:
            message_id (str): The ID of the message to get attachments from

        Returns:
            list[str]: List of file paths to the saved PDF attachments
        """
        attachments = self._get_pdf_attachments(message_id)
        file_paths = []

        for attachment in attachments:
            download_path = get_temp_dir() / attachment.filename
            with open(download_path, "wb") as f:
                f.write(attachment.data)
            file_paths.append(download_path.as_posix())

        return file_paths

    def download_pdf_attachments_to_ram(self, message_id) -> List[MemoryAttachment]:
        """
        Download all PDF attachments from a given message into memory.

        Args:
            message_id (str): The ID of the message to get attachments from

        Returns:
            List[MemoryAttachment]: List of MemoryAttachment objects containing
            attachment details with filename and content (BytesIO object)
        """
        attachments = self._get_pdf_attachments(message_id)
        memory_files = []

        for attachment in attachments:
            file_obj = BytesIO(attachment.data)
            memory_files.append(
                MemoryAttachment(filename=attachment.filename, content=file_obj)
            )

        return memory_files

    def get_recent_emails(self, days=2):
        """
        Fetch emails received in the last specified days.

        Args:
            days (int): Number of days to look back (default: 2)

        Returns:
            list: List of dictionaries containing email details
        """
        # Calculate time threshold
        time_threshold = datetime.now(timezone.utc) - timedelta(days=days)

        # Build query
        query = GmailQueryBuilder().after_date(time_threshold).build()

        messages = self._query_messages_ids(query)
        emails = []

        for message in messages:
            msg_details = self._fetch_message_details(
                message.id,
                format="metadata",
                metadata_headers=["From", "Subject", "Date"],
            )

            if msg_details:
                headers = msg_details["payload"]["headers"]
                email_data = {
                    "id": message.id,
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

    def query_messages_with_body(self, query: str) -> list[str]:
        """
        Query messages using Gmail API with the given query and return their body.

        Args:
            query (str): Gmail search query

        Returns:
            list: List of message bodies
        """
        messages = self._query_messages_ids(query)
        message_bodies = []

        for message in messages:
            msg_details = self._fetch_message_details(message.id)
            if msg_details:
                if "parts" in msg_details["payload"]:
                    parts = msg_details["payload"]["parts"]
                    body = ""
                    for part in parts:
                        if part["mimeType"] == "text/html":
                            body = base64.urlsafe_b64decode(
                                part["body"]["data"].encode("utf-8")
                            ).decode("utf-8")
                            break
                else:
                    body = base64.urlsafe_b64decode(
                        msg_details["payload"]["body"]["data"].encode("utf-8")
                    ).decode("utf-8")

                message_bodies.append(body)

        return message_bodies

    def get_winsim_invoice_messages(self, hours=1) -> list[str]:
        """
        Fetch WinSIM invoice notification emails from the last specified hours.

        Args:
            hours (int): Number of hours to look back (default: 1)

        Returns:
            list[dict]: List of dictionaries containing message IDs and invoice details
                Each dict contains:
                - id: The Gmail message ID
                - invoice_number: The invoice number extracted from the PDF filename
                - date: The date of the email
        """
        # Calculate time threshold
        time_threshold = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Build query
        query = (
            GmailQueryBuilder()
            .from_email("no-reply@winsim.de")
            .subject("Ihre winSIM-Rechnung", exact=True)
            .after_date(time_threshold)
            .build()
        )

        messages = self._query_messages_ids(query)

        return [msg.id for msg in messages]
