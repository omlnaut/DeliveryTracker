import datetime

import telegram
from function_app import app

import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import logging


def _load_token() -> str:
    key_vault_url = "https://omlnaut-vaultier.vault.azure.net/"
    secret_name = "TelegramBotToken"  # The name of your secret in Key Vault

    # Create a secret client using the DefaultAzureCredential
    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=key_vault_url, credential=credential)

    token = secret_client.get_secret(secret_name).value or ""

    return token


@app.function_name(name="TestSendTelegramMessage")
@app.route(route="TestSendTelegramMessage")
@app.event_grid_output(
    arg_name="output",
    event_name="TestSendTelegramMessage",
    topic_endpoint_uri="SENDTELEGRAMMESSAGE_EVENT_GRID_URI",
    topic_key_setting="SENDTELEGRAMMESSAGE_EVENT_GRID_KEY",
)
def TestSendTelegramMessage(
    req: func.HttpRequest, output: func.Out[func.EventGridOutputEvent]
) -> func.HttpResponse:
    logging.info("Python event trigger function processed a request.")
    output.set(
        func.EventGridOutputEvent(
            id="test-id",
            data={"message": "hello there testi"},
            subject="test-subject",
            event_type="test-event-1",
            event_time=datetime.datetime.now(),
            data_version="1.0",
        )
    )

    return func.HttpResponse("yay")


@app.event_grid_trigger(arg_name="azeventgrid")
async def SendTelegramMessage(azeventgrid: func.EventGridEvent):
    logging.info("Python EventGrid trigger processed an event")
    data = azeventgrid.get_json()
    msg = data["message"]

    token = _load_token()
    chat_id = 190599017

    bot = telegram.Bot(token)
    async with bot:
        await bot.send_message(text=msg, chat_id=chat_id)

    logging.info(f"Telegram Message sent: {msg}")
