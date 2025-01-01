from datetime import datetime
import logging
import json
from dataclasses import dataclass
from fp.fp import FreeProxy

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


def _fetch_with_proxy(url: str, headers: dict) -> requests.Response:
    for _ in range(3):
        proxy = FreeProxy().get()
        response = requests.get(url, headers=headers, proxies={"http": proxy})

        if response.status_code == 200:
            logging.info(f"Successfully fetched with proxy: {url}")
            return response

    raise Exception(f"Failed to fetch with proxy: {url}")


def _has_chapter_for_today(series_id: int) -> str | None:
    """Check if there is a new chapter today for the given series ID.

    Args:
        series_id: The series ID from the FlameComics URL

    Returns:
        The chapter number if there is an update today, None otherwise
    """
    url = f"http://flamecomics.xyz/series/{series_id}"
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "de-DE,de;q=0.9,en-US;q=0.8,en-DE;q=0.7,en;q=0.6",
        "cookie": "cf_clearance=xBO_P87WodUZXV.8QsJFjQCXHRPclu9bMNxBDVCSkkk-1735678421-1.2.1.1-qHhrc1y.k2AOZwDmPKRgrfKsfQflpOU5RAT3345qHh239Cu.NbvwkpWNYJEo03rgXkvcZ5fhYqnVVuB6dOHj9uQ3HHuWkKfsAsxbka0Bbpub9Qg4xCFgBfOZPV_.50DYiGdsS1hVab7_WMqWe.z9fdu7ubdwl_L9.BvIWR0f_NjNzYgpNunC8YCH1W_ghtX3V_ZefHDeea30HQ23nqGhQWVSTZx7dK_Gks8IwGo9mPQSNjqgxnei9DmvKeVtIZIbEsZ5BIl2MwZ7twi6.B5.7IRzaggNy6_k5Wu8dF2rcfAQvjBzWpFhYuH3R5qGElyOuGWGScVQE3d22q7.D_Ukwd63yHoZA32w0euMRH581Y_zS9q7_ixubTnO_LcwNrvxUGQ.bRWNd5c3Kb6ViOvx5g",
        "dnt": "1",
        "priority": "u=0, i",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }
    response = _fetch_with_proxy(url, headers)
    html = response.content.decode()

    soup = BeautifulSoup(html, "html.parser")
    script = soup.find(
        "script", attrs={"id": "__NEXT_DATA__", "type": "application/json"}
    )
    if not script or not script.contents:
        logging.warning(f"Could not find Next.js data for series {series_id}")
        logging.warning(html)
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
