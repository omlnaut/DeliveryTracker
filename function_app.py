import azure.functions as func
import logging

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="http_to_log")
def http_to_log(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Processing request", extra={"FunctionName": "TestiFunc", "Environment": "Production"})

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )

import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

@app.route(route="get_secret")
def get_secret(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    # The URL of your Key Vault
    key_vault_url = "https://omlnaut-vaultier.vault.azure.net/"
    secret_name = "mysecret"  # The name of your secret in Key Vault

    # Create a secret client using the DefaultAzureCredential
    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=key_vault_url, credential=credential)

    try:
        # Retrieve the secret value
        secret = secret_client.get_secret(secret_name)
        logging.info(f"Retrieved secret value: {secret.value}")
        return func.HttpResponse(f"The secret value is: {secret.value}", status_code=200)
    except Exception as e:
        logging.error("Failed to retrieve the secret.")
        logging.error(str(e))
        return func.HttpResponse("Error retrieving secret.", status_code=500)
