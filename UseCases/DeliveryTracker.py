from datetime import datetime
import json
import logging

from google.oauth2.credentials import Credentials

import azure.functions as func

from Infrastructure.telegram.azure_helper import (
    create_telegram_output_event,
    telegram_output_binding,
)
from function_app import app
from shared.GoogleServices import GmailService, TaskService
from shared.AzureHelper import get_secret


def _load_credentials() -> Credentials:
    secret_str = get_secret("GcloudCredentials")

    credentials_info = json.loads(secret_str)  # type: ignore

    return Credentials.from_authorized_user_info(credentials_info)


@app.timer_trigger(schedule="5 * * * *", arg_name="mytimer", run_on_startup=False)
@telegram_output_binding()
def dhl_mail_to_task(
    mytimer: func.TimerRequest, telegramOutput: func.Out[func.EventGridOutputEvent]
):
    credentials = _load_credentials()
    gmail_service = GmailService(credentials)
    task_service = TaskService(credentials)

    dhl_mails = gmail_service.get_amazon_dhl_pickup_emails(hours=1)
    if not dhl_mails:
        nothing_new_msg = "No DHL pickup notifications found"
        logging.info({"message": nothing_new_msg})
        return

    # create tasks
    default_tasklist_id = task_service.get_default_tasklist()

    for mail in dhl_mails:
        notes = (
            f"Abholort: {mail['pickup_location']}\n"
            f"Abholen bis: {mail['due_date']}\n"
            f"Tracking: {mail['tracking_number']}"
        )
        task = task_service.create_task_with_notes(
            tasklist_id=default_tasklist_id,
            title="Paket abholen",
            notes=notes,
        )
        task_date_str: str = task["due"].split("T")[0]

        log_data = {
            "message": "Created task for package",
            "tracking_number": mail["tracking_number"],
            "due": task_date_str,
        }

        telegramOutput.set(
            create_telegram_output_event(
                message=f"Created Task: Paket abholen ({task_date_str})",
                subject="dhl_mail_to_task",
            )
        )

        logging.info(json.dumps(log_data))
