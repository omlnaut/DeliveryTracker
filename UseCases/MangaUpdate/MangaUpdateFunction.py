import azure.functions as func
import logging
from .MangaUpdateService import (
    MangaPublisher,
    MangaUpdateManga,
    MangaUpdateService,
    mangas,
)
from function_app import app

mangas = [
    MangaUpdateManga(
        title="Omniscient Reader's Viewpoint",
        url="https://flamecomics.xyz/series/2",
        series_id=50369844984,
        publisher=MangaPublisher.FLAMECOMICS,
    ),
]


@app.route(route="test_mangaupdate")
def test_mangaupdate(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("MangaUpdate login function processed a request.")

    try:
        service = MangaUpdateService()
        latest_chapter = service.get_latest_chapter(mangas[0])

        response_data = {
            "manga_title": mangas[0].title,
            "chapter": latest_chapter.chapter,
            "release_date": latest_chapter.release_date.strftime("%Y-%m-%d"),
            "chapter_title": latest_chapter.title,
        }

        return func.HttpResponse(str(response_data), status_code=200)
    except Exception as e:
        logging.error(f"Operation failed: {str(e)}")
        return func.HttpResponse(f"Operation failed: {str(e)}", status_code=500)
