import datetime
from function_app import app

import azure.functions as func
import logging


@app.function_name(name="TestSendTelegramMessage")
@app.route(route="TestSendTelegramMessage")
@app.event_grid_output(
    arg_name="output",
    event_name="TestSendTelegramMessage",
    topic_endpoint_uri="EVENT_GRID_TOPIC_ENDPOINT_URI",
    topic_key_setting="EVENT_GRID_KEY",
)
def TestSendTelegramMessage(
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


@app.event_grid_trigger(arg_name="azeventgrid")
def SendTelegramMessage(azeventgrid: func.EventGridEvent):
    logging.info("Python EventGrid trigger processed an event")
