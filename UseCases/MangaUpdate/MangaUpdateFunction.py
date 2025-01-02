import azure.functions as func
import logging
from .MangaUpdateService import (
    MangaPublisher,
    MangaUpdateManga,
    MangaUpdateService,
    mangas,
)
from function_app import app
from Infrastructure.google_task.azure_helper import (
    create_task_output_event,
    TaskListType,
    task_output_binding,
)
from shared.date_utils import is_at_most_one_day_old

mangas = [
    MangaUpdateManga(
        title="Omniscient Reader's Viewpoint",
        url="https://flamecomics.xyz/series/2",
        series_id=50369844984,
        publisher=MangaPublisher.FLAMECOMICS,
    ),
    MangaUpdateManga(
        title="Auto Hunting with Clones",
        url="https://flamecomics.xyz/series/109",
        series_id=44327338345,
        publisher=MangaPublisher.FLAMECOMICS,
    ),
    MangaUpdateManga(
        title="Solo Leveling Ragnarok",
        url="https://reaperscans.com/series/solo-leveling-ragnarok",
        series_id=47955563021,
        publisher=MangaPublisher.REAPERSCANS,
    ),
    MangaUpdateManga(
        title="Level up with skills",
        url="https://reaperscans.com/series/level-up-with-skills",
        series_id=62165182260,
        publisher=MangaPublisher.REAPERSCANS,
    ),
    MangaUpdateManga(
        title="Infinite Mage",
        url="https://reaperscans.com/series/infinite-mage-941",
        series_id=32357730076,
        publisher=MangaPublisher.REAPERSCANS,
    ),
    MangaUpdateManga(
        title="One Piece",
        url="https://mangaplus.shueisha.co.jp/titles/100020",
        series_id=55099564912,
        publisher=MangaPublisher.MANGAPLUS,
    ),
]


@app.timer_trigger(schedule="7 6 * * *", arg_name="mytimer", run_on_startup=False)
@task_output_binding()
def manga_update(
    mytimer: func.TimerRequest,
    taskOutput: func.Out[func.EventGridOutputEvent],
) -> None:
    logging.info("MangaUpdate timer function processed a request.")

    service = MangaUpdateService()

    for manga in mangas:
        try:
            latest_chapter = service.get_latest_chapter(manga)
            logging.info(
                f"Latest chapter for {manga.title}: Chapter {latest_chapter.chapter} ({latest_chapter.release_date.strftime('%Y-%m-%d')})"
            )

            if is_at_most_one_day_old(latest_chapter.release_date):
                taskOutput.set(
                    create_task_output_event(
                        title=f"{manga.title} Chapter {latest_chapter.chapter}",
                        notes=manga.url,
                        tasklist=TaskListType.MANGA,
                    )
                )
                logging.info(
                    f"Created task for {manga.title} Chapter {latest_chapter.chapter}"
                )

        except Exception as e:
            logging.error(f"Failed to process manga {manga.title}: {str(e)}")
