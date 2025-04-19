from io import BytesIO
from typing import Generator
import requests
from bs4 import BeautifulSoup

from UseCases.mietplan.FileMetadata import FileMetadata
from UseCases.mietplan.FolderMetadata import FolderMetadata
from UseCases.mietplan.models import File, Folder
from shared.AzureHelper.download import get_temp_dir

# Constants
LOGIN_CSRF_URL = "https://mietplan-dresden.de/login/"
MAIN_FOLDER_ID = "ac4do35ktgfi79j8ids35om8udm"


def extract_csrf_token(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    input_element = soup.find("input", {"name": "csrf"})
    if input_element is None:
        raise ValueError("No login form found for csrf token")

    csrf_token = input_element["value"]  # type: ignore
    if not csrf_token:
        raise ValueError("Empty CSRF token found in the login form")

    return str(csrf_token)


def fetch_csrf_token(session: requests.Session) -> str:
    response = session.get(LOGIN_CSRF_URL)
    response.raise_for_status()
    return extract_csrf_token(response.content.decode(encoding="latin-1"))


def login(session: requests.Session, username: str, password: str) -> None:
    csrf_token = fetch_csrf_token(session)
    login_url = "https://mietplan-dresden.de/auctores/scs/auctores.controller.web.InfoLoginMultiController"

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en-DE;q=0.7,en;q=0.6",
        "Cache-Control": "max-age=0",
        "Origin": "https://mietplan-dresden.de",
        "Referer": "https://mietplan-dresden.de/login/",
        "DNT": "1",
        "Sec-CH-UA": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    }

    data = {
        "csrf": csrf_token,
        "fdInf_ID": "CY25277299X1116e405343XY7477",
        "fdCtrlType": "FORWARDER",
        "fdMode": "MODE_LOGIN",
        "dbUserID": username,
        "dbPasswort": password,
    }

    response = session.post(login_url, headers=headers, data=data)
    response.raise_for_status()


def get_folders(
    session: requests.Session, parent_folder_id: str
) -> list[FolderMetadata]:
    url = f"https://mietplan-dresden.de/moxanos/json?&svc=org.auctores.bvi.mietplan2&msg=getFolders&fdFolder={parent_folder_id}"
    response = session.get(url)
    response.raise_for_status()
    return [
        FolderMetadata.from_json(folder_json)
        for folder_json in response.json().values()
    ]


def get_files(session: requests.Session, folder_id: str) -> list[FileMetadata]:
    url = f"https://mietplan-dresden.de/moxanos/json?&svc=org.auctores.bvi.mietplan2&msg=getFiles&fdFolder={folder_id}"
    response = session.get(url)
    response.raise_for_status()
    return [FileMetadata.from_json(file_json) for file_json in response.json().values()]


def download_file_to_ram(
    session: requests.Session, download_path: str, filename: str
) -> BytesIO:
    download_base = "https://mietplan-dresden.de"
    download_url = download_base + download_path
    response = session.get(download_url)

    response.raise_for_status()  # Ensure the request was successful

    file_in_memory = BytesIO(response.content)
    return file_in_memory


def walk_from_top_folder(
    session: requests.Session, top_folder_id: str
) -> Generator[Folder, None, None]:
    """
    Walk through all folders recursively starting from the top folder.
    Yields each folder with its files and full path.

    Args:
        session: Authenticated session
        top_folder_id: ID of the starting folder

    Yields:
        Folder: Contains folder info, path and files
    """
    folders_to_check = [
        Folder(folder.folder_id, [folder.name], [])
        for folder in get_folders(session, top_folder_id)
    ]

    while folders_to_check:
        folder = folders_to_check.pop()

        # Get files in current folder
        files = get_files(session, folder.id)
        for file in files:
            folder.files.append(
                File(file.creation_date, file.filename, file.download_path)
            )

        yield folder

        # Check for subfolders and add them to processing queue
        sub_folders = get_folders(session, folder.id)
        for sub_folder in sub_folders:
            folders_to_check.append(
                Folder(sub_folder.folder_id, folder.path + [sub_folder.name], [])
            )
