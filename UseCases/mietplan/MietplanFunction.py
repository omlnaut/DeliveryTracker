import json
import azure.functions as func
import requests

from UseCases.mietplan.session_handling import MAIN_FOLDER_ID, get_folders, login
from function_app import app
from shared.AzureHelper.secrets import get_secret


@app.route(route="mietplan")
def mietplan(req: func.HttpRequest):
    username = get_secret("MietplanUsername")
    password = get_secret("MietplanPassword")

    session = requests.Session()

    login(session, username, password)

    folders = get_folders(session, MAIN_FOLDER_ID)
    folders_str = "\n".join([str(folder) for folder in folders])

    return func.HttpResponse(folders_str)
