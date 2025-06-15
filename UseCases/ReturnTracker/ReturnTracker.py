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
from UseCases.ReturnTracker.fetch_mail import get_amazon_return_mails
from UseCases.ReturnTracker.parsing import parse_return_info
from function_app import app
from shared.GoogleServices import GmailService
from shared.AzureHelper import get_secret


def _load_credentials() -> Credentials:
    secret_str = get_secret("GcloudCredentials")

    credentials_info = json.loads(secret_str)  # type: ignore

    return Credentials.from_authorized_user_info(credentials_info)


@app.timer_trigger(
    schedule="35 * * * *", arg_name="mytimer", run_on_startup=False, use_monitor=False
)
@task_output_binding()
@telegram_output_binding()
def return_tracker(
    mytimer: func.TimerRequest,
    taskOutput: func.Out[func.EventGridOutputEvent],
    telegramOutput: func.Out[func.EventGridOutputEvent],
):
    try:
        credentials = _load_credentials()
        gmail_service = GmailService(credentials)

        raw_mails = get_amazon_return_mails(gmail_service, hours=1)

        logging.info(f"Found {len(raw_mails)} DHL return notifications")

        tasks: list[func.EventGridOutputEvent] = []
        for mail in raw_mails:
            parsed_mail = parse_return_info(mail)
            notes = (
                f"{parsed_mail.item_title}\n"
                f"Abholort: {parsed_mail.pickup_location}\n"
                f"Retoure bis: {parsed_mail.return_date}\n"
                f"Order: {parsed_mail.order_number}"
            )
            tasks.append(create_task_output_event(title="Retoure", notes=notes))

        taskOutput.set(tasks)  # type: ignore
    except Exception as e:
        logging.error(str(e))

        telegramOutput.set(
            create_telegram_output_event(message=f"Error in return_tracker: {str(e)}")
        )
