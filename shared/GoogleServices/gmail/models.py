"""Models for Gmail service."""

from dataclasses import dataclass
from io import BytesIO


@dataclass
class MessageId:
    """Class to represent a Gmail message ID and its corresponding thread ID."""

    id: str
    thread_id: str


@dataclass
class AttachmentData:
    """Dataclass to represent an attachment with its filename and binary data."""

    filename: str
    data: bytes


@dataclass
class MemoryAttachment:
    """Dataclass to represent an attachment in memory with filename and BytesIO content."""

    filename: str
    content: BytesIO
