import datetime
import uuid

import telegram
from function_app import app

import azure.functions as func
import logging

from shared.AzureHelper.secrets import get_secret


def _load_token() -> str:
    return get_secret("TelegramBotToken")


def telegram_output_binding(arg_name="output"):
    return app.event_grid_output(
        arg_name=arg_name,
        event_name="send_telegram_message",
        topic_endpoint_uri="SENDTELEGRAMMESSAGE_EVENT_GRID_URI",
        topic_key_setting="SENDTELEGRAMMESSAGE_EVENT_GRID_KEY",
    )


def create_telegram_output_event(
    message: str, subject: str = "send_telegram_message"
) -> func.EventGridOutputEvent:
    return func.EventGridOutputEvent(
        id=str(uuid.uuid4()),
        data={"message": message},
        subject=subject,
        event_type="send_telegram_message_event",
        event_time=datetime.datetime.now(),
        data_version="1.0",
    )


@app.route(route="test_send_telegram_message")
@telegram_output_binding()
def test_send_telegram_message(
    req: func.HttpRequest, output: func.Out[func.EventGridOutputEvent]
) -> func.HttpResponse:
    logging.info("Python event trigger function processed a request.")
    output.set(create_telegram_output_event(message="hello there testi"))

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
