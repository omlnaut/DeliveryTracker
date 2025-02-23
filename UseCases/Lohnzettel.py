import logging
from pathlib import Path
from Infrastructure.google_task.azure_helper import (
    create_task_output_event,
    task_output_binding,
)
from function_app import app

import azure.functions as func

from shared.AzureHelper.secrets import load_gcloud_credentials
from shared.GoogleServices import GmailService
from shared.GoogleServices.GmailQueryBuilder import GmailQueryBuilder


@app.route(route="save_lohnzettel")
def save_lohnzettel(req: func.HttpRequest):
    credentials = load_gcloud_credentials()
    gmail_service = GmailService(credentials)

    query = (
        GmailQueryBuilder()
        .from_email("personal@relaxdays.de")
        .subject("Lohnschein/Korrekturlohnschein")
        .has_attachment()
        .build()
    )

    message_ids = [message["id"] for message in gmail_service._query_messages(query)]

    for msg_id in message_ids:
        file_paths = [
            Path(path) for path in gmail_service.download_pdf_attachments(msg_id)
        ]

        logging.info(f"Downloaded {file_paths} attachments from message {msg_id}")

        for file_path in file_paths:
            file_path.unlink()

        break

    return func.HttpResponse("yay")
