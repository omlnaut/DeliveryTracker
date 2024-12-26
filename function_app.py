import datetime
import azure.functions as func
import logging


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

import UseCases.DeliveryTracker
import Infrastructure.Telegram
