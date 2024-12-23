import datetime
import json
import azure.functions as func
import logging
from google.oauth2.credentials import Credentials
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from TaskService import TaskService
from gmail_service import GmailService

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


def _load_credentials() -> Credentials:
    key_vault_url = "https://omlnaut-vaultier.vault.azure.net/"
    secret_name = "GcloudCredentials"  # The name of your secret in Key Vault

    # Create a secret client using the DefaultAzureCredential
    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=key_vault_url, credential=credential)

    secret_str = secret_client.get_secret(secret_name).value
    credentials_info = json.loads(secret_str)  # type: ignore

    return Credentials.from_authorized_user_info(credentials_info)


@app.timer_trigger(schedule="5 * * * *", arg_name="mytimer", run_on_startup=False)
def http_to_log(mytimer: func.TimerRequest):
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
        log_data = {
            "message": "Created task for package",
            "tracking_number": mail["tracking_number"],
            "due": str(task["due"]),
        }

        # Convert dictionary to a JSON string before logging
        logging.info(json.dumps(log_data))


@app.route(route="event_trigger_testi")
@app.event_grid_output(
    arg_name="output",
    event_name="event_trigger_testi",
    topic_endpoint_uri="EVENT_GRID_TOPIC_ENDPOINT_URI",
    topic_key_setting="EVENT_GRID_KEY",
)
def event_trigger_testi(
    req: func.HttpRequest, output: func.Out[func.EventGridOutputEvent]
) -> func.HttpResponse:
    logging.info("Python event trigger function processed a request.")
    output.set(
        func.EventGridOutputEvent(
            id="test-id",
            data={"tag1": "value1", "tag2": "value2"},
            subject="test-subject",
            event_type="test-event-1",
            event_time=datetime.datetime.now(),
            data_version="1.0",
        )
    )

    return func.HttpResponse("yay")


@app.event_grid_trigger(
    arg_name="azeventgrid",
)
def EventGridTriggerTesti(azeventgrid: func.EventGridEvent):
    logging.info("Python EventGrid trigger processed an event")
    logging.info(azeventgrid.get_json())
