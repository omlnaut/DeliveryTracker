import datetime

import telegram
from function_app import app

import azure.functions as func
import logging

from shared.AzureHelper.secrets import get_secret


def _load_token() -> str:
    return get_secret("TelegramBotToken")


@app.route(route="test_send_telegram_message")
@app.event_grid_output(
    arg_name="output",
    event_name="test_send_telegram_message",
    topic_endpoint_uri="SENDTELEGRAMMESSAGE_EVENT_GRID_URI",
    topic_key_setting="SENDTELEGRAMMESSAGE_EVENT_GRID_KEY",
)
def test_send_telegram_message(
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
async def send_telegram_message(azeventgrid: func.EventGridEvent):
    logging.info("Python EventGrid trigger processed an event")
    data = azeventgrid.get_json()
    msg = data["message"]

    token = _load_token()
    chat_id = 190599017

    bot = telegram.Bot(token)
    async with bot:
        await bot.send_message(text=msg, chat_id=chat_id)

    logging.info(f"Telegram Message sent: {msg}")
