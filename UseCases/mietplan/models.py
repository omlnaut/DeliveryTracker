from dataclasses import dataclass
from datetime import datetime


@dataclass
class File:
    creation_date: datetime
    name: str
    url: str


@dataclass
class Folder:
    id: str
    path: list[str]
    files: list[File]
