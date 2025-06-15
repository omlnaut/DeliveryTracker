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
from Infrastructure.telegram.azure_helper import (
    create_telegram_output_event,
    telegram_output_binding,
)
from function_app import app
from shared.date_utils import is_at_most_one_day_old


def _has_chapter_for_today(html) -> str | None:
    """Return True if a chapter with today's date is found."""
    soup = BeautifulSoup(html, "html.parser")
    chapters_list = soup.find("div", {"id": "chapters-list"})
    chapter_links = chapters_list.find_all("a", class_="chplinks")  # type: ignore
    for link in chapter_links:
        span = link.find("span", style="float:right;text-align: right;")  # type: ignore
        if span:
            date_text = span.get_text(strip=True)
            date_obj = datetime.strptime(date_text, "%Y-%m-%d").date()
            if is_at_most_one_day_old(date_obj):
                chapter_number = link.get_text().split("\n")[1].strip()
                return chapter_number
    return None


@app.route(route="test_skeleton_soldier")
@telegram_output_binding()
def test_skeleton_soldier(
    req: func.HttpRequest, telegramOutput: func.Out[func.EventGridOutputEvent]
):
    logging.info("start skeleton soldier test")

    url = "https://www.reddit.com/r/SkeletonSoldier/new.json"
    headers = {"User-Agent": "script:deliverytracker:v1.0 (by /u/omlnaut)"}
    html = requests.get(url, headers=headers)
    logging.info(f"Response status code: {html.status_code}")

    telegramOutput.set(
        create_telegram_output_event(
            message=f"Skeleton Soldier test response status code: {html.status_code}"
        )
    )
    if html.status_code != 200:
        logging.info(html.content.decode("utf-8"))
        return func.HttpResponse(
            "Failed to fetch data from Reddit", status_code=html.status_code
        )
    json = html.json()

    from datetime import datetime, timezone

    for child in json["data"]["children"]:
        data = child["data"]
        created_datetime = datetime.fromtimestamp(data["created_utc"], timezone.utc)
        flair = data["link_flair_text"]
        title = data["title"]

        response_parts = []
        if flair is not None and flair.lower() == "new chapter":
            print(f"{created_datetime} - {title}")
            response_parts.append(f"{created_datetime} - {title}")

    response = "\n".join(response_parts)
    return func.HttpResponse(response)


# @app.timer_trigger(
#     schedule="7 6 * * *", arg_name="mytimer", run_on_startup=False, use_monitor=False
# )
# @task_output_binding()
# @telegram_output_binding()
def skeleton_soldier_update(
    mytimer: func.TimerRequest,
    taskOutput: func.Out[func.EventGridOutputEvent],
    telegramOutput: func.Out[func.EventGridOutputEvent],
):
    try:
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
    except Exception as e:
        logging.error(str(e))
        telegramOutput.set(
            create_telegram_output_event(
                message=f"Error in skeleton_soldier_update: {str(e)}"
            )
        )
