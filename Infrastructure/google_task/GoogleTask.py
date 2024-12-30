import logging
from .azure_helper import (
    TaskListType,
    task_output_binding,
    create_task_output_event,
    app,
)
from Infrastructure.telegram.azure_helper import (
    create_telegram_output_event,
    telegram_output_binding,
)

import azure.functions as func
import json

from google.oauth2.credentials import Credentials
from shared.AzureHelper import get_secret
from shared.GoogleServices import TaskService


def _load_credentials() -> Credentials:
    secret_str = get_secret("GcloudCredentials")

    credentials_info = json.loads(secret_str)  # type: ignore

    return Credentials.from_authorized_user_info(credentials_info)


@app.route(route="test_create_task")
@task_output_binding()
def test_create_task(
    req: func.HttpRequest, taskOutput: func.Out[func.EventGridOutputEvent]
):
    logging.info("Python event trigger function processed a request.")
    taskOutput.set(
        create_task_output_event(
            title="test title", notes="test notes", tasklist=TaskListType.MANGA
        )
    )

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
    task_list = data["tasklist"]

    task_service = TaskService(_load_credentials())

    task = task_service.create_task_with_notes(
        tasklist_id=task_list,
        title=title,
        notes=notes,
    )

    logging.info(f"Task created: {task}")

    task_date_str: str = task["due"].split("T")[0]
    task_list_type = TaskListType(task_list)
    task_list_name = task_list_type.name
    telegramOutput.set(
        create_telegram_output_event(
            message=f"Task created in {task_list_name}: {title} ({task_date_str})"
        )
    )
