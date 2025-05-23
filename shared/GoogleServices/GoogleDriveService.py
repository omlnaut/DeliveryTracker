from pathlib import Path
from typing import Optional
from io import BytesIO
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload


class GoogleDriveService:
    """Service class for interacting with Google Drive API"""

    def __init__(self, credentials):
        """
        Initialize the Google Drive service.

        Args:
            credentials: Google OAuth2 credentials
        """
        self.credentials = credentials
        self.service = None

    def authenticate(self):
        """Authenticate with Google Drive API."""
        self.service = build(
            "drive", "v3", credentials=self.credentials, cache_discovery=False
        )

    def upload_file_from_path(
        self,
        file_path: str | Path,
        drive_folder_id: str,
        mime_type: Optional[str] = None,
        custom_filename: Optional[str] = None,
    ) -> str:
        """
        Upload a file to a specific Google Drive folder.

        Args:
            file_path: Path to the file to upload
            drive_folder_id: ID of the Google Drive folder to upload to
            mime_type: Optional MIME type of the file. If not provided, will be guessed from the file extension
            custom_filename: Optional custom filename to use in Google Drive. If not provided, uses the original filename

        Returns:
            str: ID of the uploaded file in Google Drive

        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the service is not authenticated
            Exception: If there's an error during upload
        """
        if not self.service:
            self.authenticate()

        # Convert to Path object for easier handling
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Determine filename
        filename = custom_filename or file_path.name

        # Determine MIME type if not provided
        if not mime_type:
            # Common MIME types mapping
            mime_types = {
                ".pdf": "application/pdf",
                ".doc": "application/msword",
                ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ".xls": "application/vnd.ms-excel",
                ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".txt": "text/plain",
                ".csv": "text/csv",
            }
            mime_type = mime_types.get(
                file_path.suffix.lower(), "application/octet-stream"
            )

        try:
            # Prepare file metadata
            file_metadata = {"name": filename, "parents": [drive_folder_id]}

            # Create media upload object
            media = MediaFileUpload(
                str(file_path),
                mimetype=mime_type,
                resumable=True,  # Enable resumable uploads for larger files
            )

            # Upload the file
            uploaded_file = (
                self.service.files()  # type: ignore
                .create(
                    body=file_metadata,
                    media_body=media,
                    fields="id",  # Only return the file ID
                )
                .execute()
            )

            return uploaded_file.get("id")

        except Exception as e:
            raise Exception(f"Error uploading file to Google Drive: {str(e)}")

    def upload_file_directly(
        self,
        file_content: BytesIO,
        filename: str,
        drive_folder_id: str,
        mime_type: str = "application/octet-stream",
    ) -> str:
        """
        Upload file content directly to Google Drive without requiring a file on disk.

        Args:
            file_content: BytesIO object containing the file content
            filename: Name to use for the file in Google Drive
            drive_folder_id: ID of the Google Drive folder to upload to
            mime_type: MIME type of the file (defaults to application/octet-stream)

        Returns:
            str: ID of the uploaded file in Google Drive

        Raises:
            ValueError: If the service is not authenticated or if params are invalid
            Exception: If there's an error during upload
        """
        if not self.service:
            self.authenticate()

        if not filename:
            raise ValueError("Filename must be provided")

        try:
            # Prepare file metadata
            file_metadata = {"name": filename, "parents": [drive_folder_id]}

            # Create media upload object from BytesIO
            media = MediaIoBaseUpload(file_content, mimetype=mime_type, resumable=True)

            # Upload the file
            uploaded_file = (
                self.service.files()  # type: ignore
                .create(
                    body=file_metadata,
                    media_body=media,
                    fields="id",  # Only return the file ID
                )
                .execute()
            )

            return uploaded_file.get("id")

        except Exception as e:
            raise Exception(f"Error uploading file content to Google Drive: {str(e)}")

    def create_folder(
        self, folder_name: str, parent_folder_id: Optional[str] = None
    ) -> str:
        """
        Create a new folder in Google Drive.

        Args:
            folder_name: Name of the folder to create
            parent_folder_id: Optional ID of the parent folder. If not provided, creates in root

        Returns:
            str: ID of the created folder

        Raises:
            ValueError: If the service is not authenticated
            Exception: If there's an error creating the folder
        """
        if not self.service:
            self.authenticate()

        try:
            file_metadata: dict[str, str | list[str]] = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
            }

            if parent_folder_id:
                file_metadata["parents"] = [parent_folder_id]

            folder = (
                self.service.files().create(body=file_metadata, fields="id").execute()  # type: ignore
            )

            return folder.get("id")

        except Exception as e:
            raise Exception(f"Error creating folder in Google Drive: {str(e)}")

    def find_or_create_folder(self, folder_name: str, parent_id: str) -> str:
        """
        Find or create a folder with the given name under the specified parent folder.

        Args:
            folder_name: Name of the folder to find or create
            parent_id: ID of the parent folder to search in

        Returns:
            str: ID of the existing or newly created folder

        Raises:
            ValueError: If the service is not authenticated
        """
        if not self.service:
            self.authenticate()

        # Search for existing folder
        query = (
            f"mimeType = 'application/vnd.google-apps.folder' "
            f"and name = '{folder_name}' "
            f"and '{parent_id}' in parents "
            f"and trashed = false"
        )

        results = (
            self.service.files()  # type: ignore
            .list(
                q=query,
                spaces="drive",
                fields="files(id, name)",
            )
            .execute()
        )

        folders = results.get("files", [])
        if len(folders) > 0:
            return folders[0]["id"]

        # Create new folder if not found
        folder_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        }
        folder = (
            self.service.files().create(body=folder_metadata, fields="id").execute()  # type: ignore
        )

        return folder.get("id")

    def get_folder_id_by_path(self, root_folder_id: str, path: list[str]) -> str:
        """
        Get or create a folder path starting from a root folder.

        Args:
            root_folder_id: ID of the starting folder
            path: List of folder names representing the path (e.g. ['sub1', 'sub2', 'sub3'])

        Returns:
            str: ID of the final folder in the path

        Raises:
            ValueError: If the service is not authenticated
        """
        if not self.service:
            self.authenticate()

        current_parent_id = root_folder_id
        for folder_name in path:
            current_parent_id = self.find_or_create_folder(
                folder_name, current_parent_id
            )
        return current_parent_id
