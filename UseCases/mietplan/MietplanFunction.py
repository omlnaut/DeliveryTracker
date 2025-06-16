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
    download_file_to_ram,
    get_folders,
    login,
    walk_from_top_folder,
)
from function_app import app
from shared.AzureHelper.google_credentials import load_gcloud_credentials
from shared.AzureHelper.secrets import get_secret
from shared.GoogleServices import GDriveService

MIETPLAN_GDRIVE_FOLDER_ID = "19gdVV_DMtdQU0xi7TgfKJCRRc4c7m0fd"


@app.timer_trigger(
    schedule="0 0 22 * * *", arg_name="myTimer", run_on_startup=False, use_monitor=False
)
@telegram_output_binding()
def mietplan(
    myTimer: func.TimerRequest, telegramOutput: func.Out[func.EventGridOutputEvent]
) -> None:
    try:
        credentials = load_gcloud_credentials()
        drive_service = GDriveService(credentials)
        username = get_secret("MietplanUsername")
        password = get_secret("MietplanPassword")

        ref_date = datetime.now()

        session = requests.Session()

        login(session, username, password)

        new_files = []
        latest_file = None
        for folder in walk_from_top_folder(session, MAIN_FOLDER_ID):
            logging.info(f"Folder: {folder.path}")
            for file in folder.files:

                # update latest_file
                if latest_file is None:
                    latest_file = file
                else:
                    latest_file = max(file, latest_file, key=lambda f: f.creation_date)

                if file.creation_date > ref_date - timedelta(days=1):
                    logging.info(f"  File: {file.name}")
                    logging.info("    Downloading...")
                    file_in_ram = download_file_to_ram(session, file.url, file.name)

                    logging.info(f"Upload to {file.name} at path {folder.path}")
                    upload_folder_id = drive_service.get_folder_id_by_path(
                        MIETPLAN_GDRIVE_FOLDER_ID, folder.path
                    )
                    drive_service.upload_file_directly(
                        file_in_ram, file.name, upload_folder_id
                    )
                    new_files.append(
                        create_telegram_output_event(
                            message=f"New mietplan file {file.name} at {folder.path}"
                        )
                    )

        logging.info(f"Latest file: {latest_file}")
        if new_files:
            telegramOutput.set(new_files)  # type: ignore
    except Exception as e:
        logging.error(str(e))
        telegramOutput.set(
            create_telegram_output_event(
                message=f"Error in mietplan function: {str(e)}"
            )
        )
