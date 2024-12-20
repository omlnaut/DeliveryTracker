import json
import logging
import os
import sys
from google.cloud import logging as glcoud_logging
from google.cloud import secretmanager
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from TaskService import TaskService
from gmail_service import GmailService

if os.environ.get("ENVIRONMENT") == "development":
    logging.basicConfig(level=logging.INFO)
else:
    client = glcoud_logging.Client(project="deliverytracker-442621")
    client.setup_logging()


def _load_credentials() -> Credentials:
    project_id = "deliverytracker-442621"
    secret_name = "omlnaut_credentials"
    version_id = "latest"

    name = f"projects/{project_id}/secrets/{secret_name}/versions/{version_id}"
    client = secretmanager.SecretManagerServiceClient()

    response = client.access_secret_version(name=name)
    credentials_info = json.loads(response.payload.data.decode("UTF-8"))
    return Credentials.from_authorized_user_info(credentials_info)


def access_secret_version(request):
    credentials = _load_credentials()

    gmail_service = GmailService(credentials)
    task_service = TaskService(credentials)

    # fetch dhl emails
    # TODO: change timeframe to something more reasonable
    dhl_mails = gmail_service.get_amazon_dhl_pickup_emails(hours=1)
    if not dhl_mails:
        nothing_new_msg = "No DHL pickup notifications found"
        logging.info({"message": nothing_new_msg})
        return nothing_new_msg, 200

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
        log_data = {
            "message": "Created task for package",
            "tracking_number": mail["tracking_number"],
            "due": str(task["due"]),
        }

        # Convert dictionary to a JSON string before logging
        logging.info(json.dumps(log_data))

    return "Ok", 200


if __name__ == "__main__":
    access_secret_version(None)
