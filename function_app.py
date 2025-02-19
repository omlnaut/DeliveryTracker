import azure.functions as func


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

import UseCases.DeliveryTracker
import UseCases.SkeletonSoldier
import UseCases.MangaUpdate
import UseCases.WinSimInvoice
from UseCases.mietplan import MietplanFunction

import Infrastructure.telegram.Telegram
import Infrastructure.google_task.GoogleTask
