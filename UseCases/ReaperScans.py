from dataclasses import dataclass
import logging
import requests
from datetime import date, datetime

from Infrastructure.google_task.azure_helper import (
    TaskListType,
    create_task_output_event,
    task_output_binding,
)
import azure.functions as func
from function_app import app
from shared.date_utils import is_at_most_one_day_old


@dataclass
class ReaperManga:
    title: str
    id: int
    link_suffix: str


_manga_ids = [
    ReaperManga("Solo Leveling Ragnaroc", 100, "solo-leveling-ragnarok"),
    ReaperManga("Level up with skills", 158, "level-up-with-skills"),
    ReaperManga("Infinite Mage", 116, "infinite-mage-941"),
]


def _get_latest_update_date(series_id: int) -> tuple[date, str]:
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "de-DE,de;q=0.9,en-US;q=0.8,en-DE;q=0.7,en;q=0.6",
        "dnt": "1",
        "origin": "https://reaperscans.com",
        "priority": "u=1, i",
        "referer": "https://reaperscans.com/",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }

    response = requests.get(
        f"https://api.reaperscans.com/chapter/query?page=1&perPage=30&query=&order=desc&series_id={series_id}",
        headers=headers,
    )
    full_response = response.json()
    newest_entry = full_response["data"][0]

    date_string = newest_entry["created_at"]
    date = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%fZ").date()

    chapter_name = newest_entry["chapter_name"]

    return (date, chapter_name)


def _get_chapter_for_today(series_id: int) -> str | None:
    (date, chapter_name) = _get_latest_update_date(series_id)

    if is_at_most_one_day_old(date):
        return chapter_name
    else:
        return None


@app.timer_trigger(schedule="8 6 * * *", arg_name="mytimer", run_on_startup=False)
@task_output_binding()
def reaper_scans_update(
    mytimer: func.TimerRequest, taskOutput: func.Out[func.EventGridOutputEvent]
):
    for manga in _manga_ids:
        chapter_name = _get_chapter_for_today(manga.id)
        series_name = manga.title
        if chapter_name:
            taskOutput.set(
                create_task_output_event(
                    title=f"{series_name}: {chapter_name}",
                    notes=f"https://reaperscans.com/series/{manga.link_suffix}",
                    tasklist=TaskListType.MANGA,
                )
            )
            logging.info(f"{series_name}: {chapter_name}")
        else:
            logging.info(f"{series_name}: No update found")
