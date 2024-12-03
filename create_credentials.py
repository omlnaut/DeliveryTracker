from google_auth_oauthlib.flow import InstalledAppFlow

# The scopes required
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar",
]


def main():
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    creds = flow.run_local_server(port=0)

    # Save the credentials for the Cloud Function
    with open("credentials.json", "w") as token:
        token.write(creds.to_json())


if __name__ == "__main__":
    main()
