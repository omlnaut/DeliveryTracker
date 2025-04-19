"""Models for Gmail service."""

from dataclasses import dataclass
from io import BytesIO
from typing import Dict, List

# German month names mapping
GERMAN_MONTHS: Dict[str, int] = {
    "Januar": 1,
    "Februar": 2,
    "März": 3,
    "April": 4,
    "Mai": 5,
    "Juni": 6,
    "Juli": 7,
    "August": 8,
    "September": 9,
    "Oktober": 10,
    "November": 11,
    "Dezember": 12,
}


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
