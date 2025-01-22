import json
import logging
from pathlib import Path
from typing import Optional

import azure.functions as func
from google.oauth2.credentials import Credentials

from Infrastructure.telegram.azure_helper import (
    create_telegram_output_event,
    telegram_output_binding,
)
from function_app import app
from shared.GoogleServices import GmailService, GDriveService
from shared.AzureHelper import get_secret


def _load_credentials() -> Credentials:
    secret_str = get_secret("GcloudCredentials")
    credentials_info = json.loads(secret_str)  # type: ignore
    return Credentials.from_authorized_user_info(credentials_info)


@app.timer_trigger(
    schedule="30 1 * * *", arg_name="mytimer", run_on_startup=False, use_monitor=False
)
@telegram_output_binding()
def check_winsim_invoices(
    mytimer: func.TimerRequest, telegramOutput: func.Out[func.EventGridOutputEvent]
):
    """
    HTTP-triggered Azure Function that:
    1. Checks for new WinSIM invoice emails
    2. Downloads any PDF attachments
    3. Uploads them to a specified Google Drive folder

    """
    try:
        # Load credentials and initialize services
        credentials = _load_credentials()
        gmail_service = GmailService(credentials)
        drive_service = GDriveService(credentials)

        # Get the Drive folder ID
        drive_folder_id = "1VGX5Wt8D3huZm3vVemjI3C6zz6W38PJr"

        # Get WinSIM invoice message IDs from the last hour
        message_ids = gmail_service.get_winsim_invoice_messages(hours=24)

        if not message_ids:
            logging.info("No new WinSIM invoice emails found")
            return

        logging.info(f"Found {len(message_ids)} WinSIM invoice emails")
        telegramOutput.set(
            create_telegram_output_event(
                message=f"Found {len(message_ids)} WinSIM invoice emails"
            )
        )

        # Process each message
        results = []
        for msg_id in message_ids:
            try:
                # Download PDF attachments
                pdf_files = gmail_service.download_pdf_attachments(msg_id)

                # Upload each PDF to Google Drive
                for pdf_file in pdf_files:
                    file_path = Path(pdf_file)
                    if not file_path.exists():
                        logging.warning(f"PDF file not found: {pdf_file}")
                        continue

                    try:
                        # Upload to Drive
                        file_id = drive_service.upload_file(
                            file_path=file_path,
                            drive_folder_id=drive_folder_id,
                            mime_type="application/pdf",
                        )

                        results.append(
                            {
                                "message_id": msg_id,
                                "pdf_filename": pdf_file,
                                "drive_file_id": file_id,
                                "status": "success",
                            }
                        )

                        # Clean up the local file
                        file_path.unlink()

                    except Exception as upload_error:
                        results.append(
                            {
                                "message_id": msg_id,
                                "pdf_filename": pdf_file,
                                "error": str(upload_error),
                                "status": "upload_failed",
                            }
                        )

            except Exception as msg_error:
                results.append(
                    {
                        "message_id": msg_id,
                        "error": str(msg_error),
                        "status": "processing_failed",
                    }
                )

    except Exception as e:
        error_msg = f"Error processing WinSIM invoices: {str(e)}"
        logging.error(error_msg)
