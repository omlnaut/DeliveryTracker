import json
import logging

from google.oauth2.credentials import Credentials

import azure.functions as func

from Infrastructure.google_task.azure_helper import (
    create_task_output_event,
    task_output_binding,
)
from Infrastructure.telegram.azure_helper import (
    create_telegram_output_event,
    telegram_output_binding,
)
from UseCases.DeliveryTracker.fetch_mail import get_amazon_dhl_pickup_emails
from UseCases.DeliveryTracker.parsing import parse_dhl_pickup_email_html
from function_app import app
from shared.GoogleServices import GmailService
from shared.AzureHelper import get_secret


def _load_credentials() -> Credentials:
    secret_str = get_secret("GcloudCredentials")

    credentials_info = json.loads(secret_str)  # type: ignore

    return Credentials.from_authorized_user_info(credentials_info)


@app.timer_trigger(
    schedule="30 * * * *", arg_name="mytimer", run_on_startup=False, use_monitor=False
)
@task_output_binding()
@telegram_output_binding()
def dhl_mail_to_task(
    mytimer: func.TimerRequest,
    taskOutput: func.Out[func.EventGridOutputEvent],
    telegramOutput: func.Out[func.EventGridOutputEvent],
):
    try:
        credentials = _load_credentials()
        gmail_service = GmailService(credentials)

        raw_mails = get_amazon_dhl_pickup_emails(gmail_service, hours=10)

        logging.info(f"Found {len(raw_mails)} DHL pickup notifications")

        tasks: list[func.EventGridOutputEvent] = []
        for mail in raw_mails:
            parsed_mail = parse_dhl_pickup_email_html(mail)
            notes = (
                f"{parsed_mail.preview}\n"
                f"Abholort: {parsed_mail.pickup_location}\n"
                f"Abholen bis: {parsed_mail.due_date}\n"
                f"Tracking: {parsed_mail.tracking_number}"
            )
            tasks.append(create_task_output_event(title="Paket abholen", notes=notes))

        taskOutput.set(tasks)  # type: ignore
    except Exception as e:
        logging.error(str(e))

        telegramOutput.set(
            create_telegram_output_event(message=f"Error in dhl_mail_to_task: {str(e)}")
        )
