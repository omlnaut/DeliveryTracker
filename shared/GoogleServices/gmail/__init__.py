"""Gmail service module for interacting with Gmail API."""

from .service import GmailService
from .models import MessageId, AttachmentData, MemoryAttachment

__all__ = [
    "GmailService",
    "MessageId",
    "AttachmentData",
    "MemoryAttachment",
]
