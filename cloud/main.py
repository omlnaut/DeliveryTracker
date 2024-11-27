# main.py

from google.cloud import secretmanager


def access_secret_version():
    # Create the Secret Manager client
    client = secretmanager.SecretManagerServiceClient()

    # Replace these variables with your own values
    project_id = "deliverytracker-442621"
    secret_name = "testi_secret"
    version_id = "latest"  # or specify a version number

    # Build the resource name of the secret version
    name = f"projects/{project_id}/secrets/{secret_name}/versions/{version_id}"

    try:
        # Access the secret version
        response = client.access_secret_version(name=name)

        # Extract the payload as a string
        payload = response.payload.data.decode("UTF-8")

        # Log the secret payload
        print(f"Secret payload: {payload}")
    except Exception as err:
        print(f"Failed to access secret version: {err}")


if __name__ == "__main__":
    access_secret_version()
