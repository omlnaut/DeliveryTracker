class FolderMetadata:
    """
    As returned by mietplan api
    """

    name: str
    folder_id: str
    has_subfolders: bool

    @staticmethod
    def from_json(json_data: dict) -> "FolderMetadata":
        metadata = FolderMetadata()
        metadata.name = json_data["filename"]
        metadata.folder_id = json_data["fileid"]
        metadata.has_subfolders = json_data["filechildren"]
        return metadata

    def __repr__(self) -> str:
        return f"FolderMetadata(name={self.name}, folder_id={self.folder_id}, has_subfolders={self.has_subfolders})"

    def __str__(self) -> str:
        return self.name
