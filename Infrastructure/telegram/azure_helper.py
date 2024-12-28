from function_app import app
import datetime
import uuid

import azure.functions as func


def telegram_output_binding(arg_name="telegramOutput"):
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
