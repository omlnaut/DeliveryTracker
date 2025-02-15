import html
from datetime import datetime


class FileMetadata:
    creation_date: datetime
    download_path: str

    @staticmethod
    def from_json(json_data: dict) -> "FileMetadata":
        metadata = FileMetadata()
        date_format = "%d.%m.%Y"
        metadata.creation_date = datetime.strptime(json_data["filecrea"], date_format)
        metadata.download_path = html.unescape(json_data["filepath"])
        return metadata

    def __repr__(self) -> str:
        return f"FileMetadata(creation_date={self.creation_date}, download_path={self.download_path})"
