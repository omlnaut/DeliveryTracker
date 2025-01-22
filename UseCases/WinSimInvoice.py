import json
import logging

import azure.functions as func
from google.oauth2.credentials import Credentials

from function_app import app
from shared.GoogleServices import GmailService
from shared.AzureHelper import get_secret


def _load_credentials() -> Credentials:
    secret_str = get_secret("GcloudCredentials")
    credentials_info = json.loads(secret_str)  # type: ignore
    return Credentials.from_authorized_user_info(credentials_info)


@app.route(route="check_winsim_invoices")
def check_winsim_invoices(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP-triggered Azure Function that checks for new WinSIM invoice emails.

    Returns:
        A JSON response containing the list of message IDs found.
    """
    try:
        # Load credentials and initialize Gmail service
        credentials = _load_credentials()
        gmail_service = GmailService(credentials)

        # Get WinSIM invoice message IDs from the last hour
        message_ids = gmail_service.get_winsim_invoice_messages(hours=1000)

        # Log the findings
        if message_ids:
            logging.info(f"Found {len(message_ids)} WinSIM invoice emails")
        else:
            logging.info("No new WinSIM invoice emails found")

        # Return the results as JSON
        return func.HttpResponse(
            json.dumps({"message_ids": message_ids}),
            mimetype="application/json",
            status_code=200,
        )

    except Exception as e:
        error_msg = f"Error checking WinSIM invoices: {str(e)}"
        logging.error(error_msg)
        return func.HttpResponse(
            json.dumps({"error": error_msg}),
            mimetype="application/json",
            status_code=500,
        )
