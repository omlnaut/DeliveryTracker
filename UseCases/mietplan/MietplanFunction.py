from datetime import datetime, timedelta
import json
import os
import logging
import azure.functions as func
import requests

from google.oauth2.credentials import Credentials

from Infrastructure.telegram.azure_helper import (
    create_telegram_output_event,
    telegram_output_binding,
)
from UseCases.mietplan.session_handling import (
    MAIN_FOLDER_ID,
    download_file,
    get_folders,
    login,
    walk_from_top_folder,
)
from function_app import app
from shared.AzureHelper.secrets import get_secret
from shared.GoogleServices import GDriveService

MIETPLAN_GDRIVE_FOLDER_ID = "19gdVV_DMtdQU0xi7TgfKJCRRc4c7m0fd"


def _load_credentials() -> Credentials:
    secret_str = get_secret("GcloudCredentials")
    credentials_info = json.loads(secret_str)  # type: ignore
    return Credentials.from_authorized_user_info(credentials_info)


@app.timer_trigger(
    schedule="0 0 22 * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False
)
@telegram_output_binding()
def mietplan(
    myTimer: func.TimerRequest, telegramOutput: func.Out[func.EventGridOutputEvent]
) -> None:
    credentials = _load_credentials()
    drive_service = GDriveService(credentials)
    username = get_secret("MietplanUsername")
    password = get_secret("MietplanPassword")

    ref_date = datetime.now()

    session = requests.Session()

    login(session, username, password)

    new_files = []
    for folder in walk_from_top_folder(session, MAIN_FOLDER_ID):
        logging.info(f"Folder: {folder.path}")
        for file in folder.files:
            # check if creation date is at most 24 hours older than the reference date

            if file.creation_date > ref_date - timedelta(days=1):
                logging.info(f"  File: {file.name}")
                logging.info("    Downloading...")
                local_filename = download_file(session, file.url)

                logging.info(f"Upload to {local_filename} at path {folder.path}")
                upload_folder_id = drive_service.get_folder_id_by_path(
                    MIETPLAN_GDRIVE_FOLDER_ID, folder.path
                )
                drive_service.upload_file(local_filename, upload_folder_id)
                os.remove(local_filename)
                new_files.append(
                    create_telegram_output_event(
                        message=f"New mietplan file {file.name} at {folder.path}"
                    )
                )

    if new_files:
        telegramOutput.set(new_files)  # type: ignore
