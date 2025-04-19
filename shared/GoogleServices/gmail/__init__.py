"""Gmail service module for interacting with Gmail API."""

from .service import GmailService
from .models import MessageId, AttachmentData, MemoryAttachment, GERMAN_MONTHS

__all__ = [
    "GmailService",
    "MessageId",
    "AttachmentData",
    "MemoryAttachment",
    "GERMAN_MONTHS",
]
