import azure.functions as func


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

from UseCases.DeliveryTracker import DeliveryTracker
from UseCases.ReturnTracker import ReturnTracker
import UseCases.SkeletonSoldier
import UseCases.MangaUpdate
import UseCases.WinSimInvoice
from UseCases.mietplan import MietplanFunction
from UseCases.Lohnzettel import save_lohnzettel

import Infrastructure.telegram.Telegram
import Infrastructure.google_task.GoogleTask
