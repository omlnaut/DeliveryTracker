import datetime
import uuid
from function_app import app

import azure.functions as func


def task_output_binding(arg_name="taskOutput"):
    return app.event_grid_output(
        arg_name=arg_name,
        event_name="create_task",
        topic_endpoint_uri="CreateTask_EVENT_GRID_URI",
        topic_key_setting="CreateTask_EVENT_GRID_KEY",
    )


from enum import Enum


class TaskListType(Enum):
    DEFAULT = "MDY0Mzc2NjgyMDc4MTc0Nzg3Mjk6MDow"
    MANGA = "WFRzM0JfdkdTXzl4WHVHNw"


def create_task_output_event(
    title: str, notes: str = "", tasklist: TaskListType = TaskListType.DEFAULT
) -> func.EventGridOutputEvent:
    return func.EventGridOutputEvent(
        id=str(uuid.uuid4()),
        data={"title": title, "notes": notes, "tasklist": tasklist.value},
        subject="create_task_event",
        event_type="create_task_event",
        event_time=datetime.datetime.now(),
        data_version="1.0",
    )
