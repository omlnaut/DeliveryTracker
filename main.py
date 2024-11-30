import logging
from google.cloud import secretmanager

# Configure the root logger
logging.basicConfig(level=logging.INFO)

def access_secret_version(request):
    # Create a logger for this function
    logger = logging.getLogger(__name__)

    # Replace these variables with your own values
    project_id = "deliverytracker-442621"
    secret_name = "testi_secret"
    version_id = "latest"  # or specify a version number

    # Create the Secret Manager client
    client = secretmanager.SecretManagerServiceClient()

    # Build the resource name of the secret version
    name = f"projects/{project_id}/secrets/{secret_name}/versions/{version_id}"

    try:
        # Access the secret version
        response = client.access_secret_version(name=name)

        # Extract the payload as a string
        payload = response.payload.data.decode("UTF-8")

        # Log the secret payload (Avoid logging sensitive data in production)
        logger.info(f"Secret payload: {payload}")

        # Return an HTTP response if this is an HTTP-triggered function
        return f"Secret payload: {payload}", 200

    except Exception as err:
        logger.error(f"Failed to access secret version: {err}")
        return f"Failed to access secret version: {err}", 500