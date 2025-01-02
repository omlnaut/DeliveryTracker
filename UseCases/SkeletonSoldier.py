from datetime import datetime
import logging

from bs4 import BeautifulSoup

import azure.functions as func
import requests

from Infrastructure.google_task.azure_helper import (
    TaskListType,
    create_task_output_event,
    task_output_binding,
)
from function_app import app
from shared.date_utils import is_at_most_one_day_old


def _has_chapter_for_today(html) -> str | None:
    """Return True if a chapter with today's date is found."""
    soup = BeautifulSoup(html, "html.parser")
    chapters_list = soup.find("div", {"id": "chapters-list"})
    chapter_links = chapters_list.find_all("a", class_="chplinks")  # type: ignore
    for link in chapter_links:
        span = link.find("span", style="float:right;text-align: right;")
        if span:
            date_text = span.get_text(strip=True)
            date_obj = datetime.strptime(date_text, "%Y-%m-%d").date()
            if is_at_most_one_day_old(date_obj):
                chapter_number = link.get_text().split("\n")[1].strip()
                return chapter_number
    return None


@app.timer_trigger(schedule="7 6 * * *", arg_name="mytimer", run_on_startup=False)
@task_output_binding()
def skeleton_soldier_update(
    mytimer: func.TimerRequest,
    taskOutput: func.Out[func.EventGridOutputEvent],
):
    url = "https://demonicscans.org/manga/Skeleton-Soldier"

    html = requests.get(url).text

    chapter_number = _has_chapter_for_today(html)
    if chapter_number:
        taskOutput.set(
            create_task_output_event(
                title=f"Skeleton Soldier {chapter_number}",
                notes=url,
                tasklist=TaskListType.MANGA,
            )
        )
        logging.info(f"Skeleton Soldier: {chapter_number}")
        return

    logging.info("Skeleton Soldier: No update found")
