from __future__ import print_function
import os.path
import pickle

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Scope for read/write access to tasks
SCOPES = ["https://www.googleapis.com/auth/tasks"]


def get_tasks_service():
    """Authenticates the user and returns the Google Tasks service."""
    creds = None
    token_pickle = "token_tasks.pickle"
    if os.path.exists(token_pickle):
        with open(token_pickle, "rb") as token:
            creds = pickle.load(token)
    # If credentials are invalid or don't exist, initiate the OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for next time
        with open(token_pickle, "wb") as token:
            pickle.dump(creds, token)
    service = build("tasks", "v1", credentials=creds)
    return service


def search_tasks(service, query_string):
    """Searches for tasks containing the query string in their notes."""
    # Get all task lists
    tasklists = service.tasklists().list(maxResults=100).execute().get("items", [])
    matching_tasks = []

    for tasklist in tasklists:
        # Get all tasks in the task list
        tasks = service.tasks().list(tasklist=tasklist["id"]).execute().get("items", [])
        for task in tasks:
            # Check if the query string is in the task's notes
            if query_string in task["title"]:
                matching_tasks.append(
                    {
                        "tasklist_id": tasklist["id"],
                        "tasklist_title": tasklist.get("title", "No Title"),
                        "task_id": task.get("id"),
                        "title": task.get("title", "No Title"),
                        "due": task.get("due", "No Due Date"),
                        "updated": task.get("updated", "No Updated Date"),
                    }
                )
    return matching_tasks


def main():
    # Initialize the Tasks API service
    service = get_tasks_service()

    # The string to search for in task descriptions
    query_string = "Paket"  # Replace with your specific string

    # Search for existing tasks containing the query string
    tasks_found = search_tasks(service, query_string)

    if tasks_found:
        print(f"Tasks containing '{query_string}':")
        for task in tasks_found:
            print(f"Task List: {task['tasklist_title']}")
            print(f"Title: {task['title']}")
            print(f"Due: {task['due']}")
            print(f"Updated: {task['updated']}")
            print("-" * 40)


if __name__ == "__main__":
    main()
