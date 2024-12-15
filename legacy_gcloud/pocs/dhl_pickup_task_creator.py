from gmail_service import GmailService
from tasks_script import get_tasks_service
from datetime import datetime, timezone


def create_task_with_notes(service, tasklist_id, title, notes, due_date=None):
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
    task = service.tasks().insert(tasklist=tasklist_id, body=task_body).execute()
    return task


def get_default_tasklist(service):
    """Gets the default task list ID."""
    tasklists = service.tasklists().list().execute()
    return tasklists["items"][0]["id"]  # Get the first (default) task list


def main():
    # Initialize Gmail service and get DHL pickup emails
    gmail = GmailService()
    pickup_emails = gmail.get_amazon_dhl_pickup_emails(days=2)

    if not pickup_emails:
        print("No new DHL pickup emails found.")
        return

    # Initialize Tasks service
    tasks_service = get_tasks_service()
    default_tasklist = get_default_tasklist(tasks_service)

    # Create tasks for each pickup email
    for email in pickup_emails:
        # Format notes with the pickup information
        notes = (
            f"Abholort: {email['pickup_location']}\n"
            f"Abholen bis: {email['due_date']}\n"
            f"Tracking: {email['tracking_number']}"
        )

        # Create the task
        task = create_task_with_notes(
            tasks_service, default_tasklist, "Paket abholen", notes
        )
        print(
            f"Created task for package with tracking number: {email['tracking_number']}"
        )


if __name__ == "__main__":
    main()
