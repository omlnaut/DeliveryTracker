from datetime import datetime
import logging
import json
from dataclasses import dataclass

from bs4 import BeautifulSoup
import requests
import azure.functions as func

from Infrastructure.google_task.azure_helper import (
    TaskListType,
    create_task_output_event,
    task_output_binding,
)
from function_app import app
from shared.date_utils import is_at_most_one_day_old


@dataclass
class FlameManga:
    title: str
    id: int


_manga_ids = [
    FlameManga("Omniscient Reader's Viewpoint", 2),
    FlameManga("Auto-Hunting With Clones", 109),
]


def _has_chapter_for_today(series_id: int) -> str | None:
    """Check if there is a new chapter today for the given series ID.

    Args:
        series_id: The series ID from the FlameComics URL

    Returns:
        The chapter number if there is an update today, None otherwise
    """
    url = f"https://flamecomics.xyz/series/{series_id}"
    response = requests.get(url)
    html = response.content.decode()

    soup = BeautifulSoup(html, "html.parser")
    script = soup.find(
        "script", attrs={"id": "__NEXT_DATA__", "type": "application/json"}
    )
    if not script or not script.contents:
        logging.warning(f"Could not find Next.js data for series {series_id}")
        return None

    data = json.loads(script.contents[0])
    try:
        latest_chapter = data["props"]["pageProps"]["chapters"][0]
        chapter_number = latest_chapter["chapter"].split(".")[0]
        release_date = datetime.fromtimestamp(latest_chapter["release_date"]).date()

        if is_at_most_one_day_old(release_date):
            return chapter_number
    except (KeyError, IndexError) as e:
        logging.warning(f"Error parsing chapter data for series {series_id}: {e}")

    return None


@app.timer_trigger(schedule="7 6 * * *", arg_name="mytimer", run_on_startup=True)
@task_output_binding()
def flame_comics_update(
    mytimer: func.TimerRequest,
    taskOutput: func.Out[func.EventGridOutputEvent],
):
    """Azure function to check for FlameComics updates."""
    base_url = "https://flamecomics.xyz/series"

    for manga in _manga_ids:
        chapter_number = _has_chapter_for_today(manga.id)
        if chapter_number:
            taskOutput.set(
                create_task_output_event(
                    title=f"{manga.title} {chapter_number}",
                    notes=f"{base_url}/{manga.id}",
                    tasklist=TaskListType.MANGA,
                )
            )
            logging.info(f"{manga.title}: {chapter_number}")
        else:
            logging.info(f"{manga.title}: No update found")
