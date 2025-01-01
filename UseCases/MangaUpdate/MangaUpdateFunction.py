import azure.functions as func
import logging
from .MangaUpdateService import MangaUpdateService

from function_app import app


@app.route(route="test_mangaupdate")
def test_mangaupdate(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("MangaUpdate login function processed a request.")

    try:
        service = MangaUpdateService()
        # If we get here, login was successful since MangaUpdateService automatically logs in during initialization
        return func.HttpResponse("yay", status_code=200)
    except Exception as e:
        logging.error(f"Login failed: {str(e)}")
        return func.HttpResponse(f"Login failed: {str(e)}", status_code=500)
