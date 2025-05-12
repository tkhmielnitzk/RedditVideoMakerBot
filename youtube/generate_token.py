import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Define the API service
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
CLIENT_SECRETS_FILE = "client_secret.json"  # Path to your client secret file
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def authenticate():
    # Run the OAuth 2.0 flow to obtain credentials
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, SCOPES)
    credentials = flow.run_local_server(port=8080)
    
    # Save the credentials to token.json
    with open('token.json', 'w') as token:
        token.write(credentials.to_json())

    print("Token generated successfully.")

if __name__ == "__main__":
    authenticate()