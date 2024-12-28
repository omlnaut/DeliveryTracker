import datetime
import logging
import uuid
from Infrastructure.telegram.azure_helper import (
    create_telegram_output_event,
    telegram_output_binding,
)
from function_app import app

import azure.functions as func
import json

from google.oauth2.credentials import Credentials
from shared.AzureHelper import get_secret
from shared.GoogleServices import TaskService


def _load_credentials() -> Credentials:
    secret_str = get_secret("GcloudCredentials")

    credentials_info = json.loads(secret_str)  # type: ignore

    return Credentials.from_authorized_user_info(credentials_info)


def create_task_output_binding(arg_name="taskOutput"):
    return app.event_grid_output(
        arg_name=arg_name,
        event_name="create_task",
        topic_endpoint_uri="CreateTask_EVENT_GRID_URI",
        topic_key_setting="CreateTask_EVENT_GRID_KEY",
    )


def create_task_output_event(title: str, notes: str = "") -> func.EventGridOutputEvent:
    return func.EventGridOutputEvent(
        id=str(uuid.uuid4()),
        data={"title": title, "notes": notes},
        subject="create_task_event",
        event_type="create_task_event",
        event_time=datetime.datetime.now(),
        data_version="1.0",
    )


@app.route(route="test_create_task")
@create_task_output_binding()
def test_create_task(
    req: func.HttpRequest, taskOutput: func.Out[func.EventGridOutputEvent]
):
    logging.info("Python event trigger function processed a request.")
    taskOutput.set(create_task_output_event(title="test title", notes="test notes"))

    return func.HttpResponse("yay")


@app.event_grid_trigger(arg_name="azeventgrid")
@telegram_output_binding()
async def create_task(
    azeventgrid: func.EventGridEvent,
    telegramOutput: func.Out[func.EventGridOutputEvent],
):
    data = azeventgrid.get_json()
    notes = data["notes"]
    title = data["title"]

    task_service = TaskService(_load_credentials())

    default_tasklist_id = task_service.get_default_tasklist()
    task = task_service.create_task_with_notes(
        tasklist_id=default_tasklist_id,
        title=title,
        notes=notes,
    )

    logging.info(f"Task created: {task}")

    task_date_str: str = task["due"].split("T")[0]
    telegramOutput.set(
        create_telegram_output_event(message=f"Task created: {title} ({task_date_str})")
    )
