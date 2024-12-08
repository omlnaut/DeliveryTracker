from datetime import datetime, timezone
from googleapiclient.discovery import build


class TaskService:
    def __init__(self, credentials):
        self.credentials = credentials
        self.service = build(
            "tasks", "v1", credentials=credentials, cache_discovery=False
        )

    def get_default_tasklist(self):
        """Gets the default task list ID."""
        tasklists = self.service.tasklists().list().execute()
        return tasklists["items"][0]["id"]  # Get the first (default) task list

    def create_task_with_notes(self, tasklist_id, title, notes, due_date=None):
        """Creates a new task in the specified task list with notes."""
        if due_date is None:
            # Set due date to end of today
            due_date = datetime.now(timezone.utc).replace(
                hour=23, minute=59, second=59, microsecond=0
            )

        task_body = {
            "title": title,
            "notes": notes,
            "due": due_date.isoformat(),
        }
        task = (
            self.service.tasks().insert(tasklist=tasklist_id, body=task_body).execute()
        )
        return task
