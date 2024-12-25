import datetime
import azure.functions as func
import logging


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.function_name(name="event_trigger_testi")
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
