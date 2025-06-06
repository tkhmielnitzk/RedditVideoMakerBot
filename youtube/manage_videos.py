# #!/usr/bin/python



#!/usr/bin/python

import sys
from pathlib import Path
import shutil
import http.client as httplib
import httplib2
import os
import random
import time
from datetime import datetime
from filelock import FileLock, Timeout
import argparse

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# --- Configuration ---
# Path to the client secrets JSON file (downloaded from Google Cloud Console)
# Should contain client_id, client_secret, etc.
CLIENT_SECRETS_FILE = Path(os.getenv("GOOGLE_CLIENT_SECRETS_FILE", "client_secret.json"))
# CLIENT_SECRETS_FILE = Path(os.getenv("GOOGLE_CLIENT_SECRETS_FILE", "../client_secret.json"))

# Path to the token JSON file (generated by generate_token.py)
# This file stores the user's access and refresh tokens.
TOKEN_FILE_PATH = Path(os.getenv("GOOGLE_TOKEN_FILE", "token.json"))

# Directory for video files
# APP_DATA_DIR = Path(os.getenv("APP_DATA_DIR", "/app/data"))
APP_DATA_DIR = Path(os.getenv("APP_DATA_DIR", "data"))
VIDEOS_TO_POST_DIR = APP_DATA_DIR / "to_post"
VIDEOS_TO_DELETE_DIR = APP_DATA_DIR / "to_delete"

# Lock file to prevent concurrent executions
LOCK_FILE_PATH = Path(os.getenv("LOCK_FILE_PATH", "/tmp/youtube_upload.lock"))

# YouTube API settings
YOUTUBE_UPLOAD_SCOPE = ["https://www.googleapis.com/auth/youtube.upload"] # Must be a list
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

# Retry settings
httplib2.RETRIES = 1
MAX_RETRIES = 10
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, httplib.NotConnected,
                        httplib.IncompleteRead, httplib.ImproperConnectionState,
                        httplib.CannotSendRequest, httplib.CannotSendHeader,
                        httplib.ResponseNotReady, httplib.BadStatusLine)
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

# --- Authentication ---
def get_authenticated_service():
    """
    Authenticates with the YouTube API using a token file.
    Relies on a pre-existing token file (TOKEN_FILE_PATH) generated via an
    initial OAuth 2.0 flow (e.g., using generate_token.py).
    This function is non-interactive and suitable for automated environments.
    """
    creds = None

    if not CLIENT_SECRETS_FILE.is_file():
        print(f"ERROR: Client secrets file not found at '{CLIENT_SECRETS_FILE}'.")
        print("Please download it from Google Cloud Console and ensure the path is correct.")
        sys.exit(1)

    if TOKEN_FILE_PATH.is_file():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE_PATH), YOUTUBE_UPLOAD_SCOPE)
        except Exception as e:
            print(f"ERROR: Could not load credentials from '{TOKEN_FILE_PATH}'. File might be corrupted or invalid.")
            print(f"Exception: {e}")
            sys.exit(1)
    else:
        print(f"ERROR: Token file '{TOKEN_FILE_PATH}' not found.")
        print(f"Please generate it first by running a manual authorization process (e.g., using a helper script like generate_token.py).")
        sys.exit(1)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print(f"Credentials from '{TOKEN_FILE_PATH}' are expired. Attempting to refresh...")
            try:
                # The Credentials object needs client_id and client_secret to refresh.
                # These should have been included when the token.json was initially created
                # if it was created by google-auth-oauthlib's flow.
                # If not, ensure your client_secret.json is the one used to generate token.json
                # and that token.json includes client_id and client_secret fields.
                creds.refresh(Request())
                print("Token refreshed successfully.")
                # Save the (potentially) updated credentials
                with open(TOKEN_FILE_PATH, 'w') as token_file_write:
                    token_file_write.write(creds.to_json())
                print(f"Updated token saved to '{TOKEN_FILE_PATH}'.")
            except Exception as e:
                print(f"ERROR: Could not refresh token using '{TOKEN_FILE_PATH}'.")
                print(f"Exception: {e}")
                print("Ensure the refresh token is valid, not revoked, and the OAuth client configuration")
                print(f"in '{CLIENT_SECRETS_FILE}' matches the one used to create the token.")
                print(f"You may need to re-authorize manually and save a new '{TOKEN_FILE_PATH}'.")
                sys.exit(1)
        else:
            print(f"ERROR: Credentials in '{TOKEN_FILE_PATH}' are invalid or missing a refresh token.")
            print(f"Please generate a new token file with a valid refresh token.")
            sys.exit(1)

    if not creds or not creds.valid: # Final check
        print("ERROR: Authentication failed. Credentials are still invalid after attempting load/refresh.")
        sys.exit(1)
    
    print("Successfully authenticated with YouTube API.")
    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=creds)

# --- YouTube Upload Logic ---
def initialize_upload(youtube, video_file_path, title, description, category, keywords, privacy_status):
    """
    Initializes and performs the video upload.
    """
    tags = None
    if keywords:
        tags = keywords.split(",")

    body = dict(
        snippet=dict(
            title=title,
            description=description,
            tags=tags,
            categoryId=category
        ),
        status=dict(
            privacyStatus=privacy_status
        )
    )

    print(f"Preparing to upload video: '{video_file_path.name}' with title: '{title}'")

    media_body = MediaFileUpload(str(video_file_path), chunksize=-1, resumable=True)
    
    insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media_body
    )

    resumable_upload(insert_request, video_file_path.name)

def resumable_upload(insert_request, video_filename):
    """
    Handles the resumable upload process with exponential backoff for retries.
    """
    response = None
    error_message = None
    retry_count = 0
    while response is None:
        try:
            print(f"Uploading chunk for '{video_filename}'... (Attempt {retry_count + 1})")
            status, response = insert_request.next_chunk()
            if response is not None:
                if 'id' in response:
                    print(f"Video id '{response['id']}' ('{video_filename}') was successfully uploaded.")
                else:
                    print(f"The upload for '{video_filename}' failed with an unexpected response: {response}")
                    sys.exit(1) # Exit if response is malformed but not an exception
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error_message = f"A retriable HTTP error {e.resp.status} occurred for '{video_filename}':\n{e.content.decode('utf-8')}"
            else:
                print(f"A non-retriable HTTP error {e.resp.status} occurred for '{video_filename}':\n{e.content.decode('utf-8')}")
                raise  # Re-raise for non-retriable HTTP errors
        except RETRIABLE_EXCEPTIONS as e:
            error_message = f"A retriable error occurred for '{video_filename}': {e}"

        if error_message:
            print(error_message)
            retry_count += 1
            if retry_count > MAX_RETRIES:
                print(f"Exceeded maximum retries ({MAX_RETRIES}) for '{video_filename}'. Giving up.")
                sys.exit(1) # Exit after max retries

            max_sleep = 2 ** retry_count
            sleep_seconds = random.uniform(0, max_sleep) # Add jitter
            print(f"Sleeping for {sleep_seconds:.2f} seconds before retrying '{video_filename}'...")
            time.sleep(sleep_seconds)
            error_message = None # Reset error for next attempt

def upload_one_video(youtube_service, video_path, title, description, category, keywords, privacy_status):
    """
    Wrapper to upload a single video.
    """
    print(f"Starting upload process for: {video_path.name}")
    if not video_path.is_file():
        print(f"ERROR: Video file not found at '{video_path}'. Skipping.")
        return False

    if privacy_status not in VALID_PRIVACY_STATUSES:
        print(f"ERROR: Invalid privacy status '{privacy_status}'. Must be one of {VALID_PRIVACY_STATUSES}. Skipping '{video_path.name}'.")
        return False

    try:
        initialize_upload(youtube_service, video_path, title, description, category, keywords, privacy_status)
        return True
    except HttpError as e:
        print(f"An HTTP error occurred during upload of '{video_path.name}': {e.resp.status} - {e.content.decode('utf-8')}")
    except Exception as e:
        print(f"An unexpected error occurred during upload of '{video_path.name}': {e}")
    return False

# --- File Management ---
def manage_videos_to_share(youtube_service, title_template, description_template, category, keywords, privacy_status):
    print(f"Checking for videos to share in '{VIDEOS_TO_POST_DIR}'...")
    VIDEOS_TO_POST_DIR.mkdir(parents=True, exist_ok=True)
    VIDEOS_TO_DELETE_DIR.mkdir(parents=True, exist_ok=True)

    list_videos_path = sorted(list(VIDEOS_TO_POST_DIR.glob("*.mp4"))) # Process in a defined order
    
    if not list_videos_path:
        print("No new videos found in to_post directory.")
        return

    one_video_path = list_videos_path[0] # Process one video per run as per original logic
    
    # Customize title and description if needed (e.g., based on filename or date)
    # For now, using the provided templates directly.
    # You could extract parts of one_video_path.name to customize title/description.
    final_title = title_template.replace("{filename}", one_video_path.stem).replace("{date}", datetime.today().strftime("%Y-%m-%d"))
    final_description = description_template.replace("{filename}", one_video_path.stem).replace("{date}", datetime.today().strftime("%Y-%m-%d"))

    print(f"Attempting to upload '{one_video_path.name}' with title '{final_title}'.")
    success = upload_one_video(youtube_service,
                               one_video_path,
                               final_title,
                               final_description,
                               category,
                               keywords,
                               privacy_status)
    if success:
        print(f"Successfully uploaded '{one_video_path.name}'. Moving to '{VIDEOS_TO_DELETE_DIR}'.")
        try:
            shutil.move(str(one_video_path), str(VIDEOS_TO_DELETE_DIR / one_video_path.name))
        except Exception as e:
            print(f"ERROR: Could not move '{one_video_path.name}' to '{VIDEOS_TO_DELETE_DIR}': {e}")
    else:
        print(f"Failed to upload '{one_video_path.name}'. It will remain in '{VIDEOS_TO_POST_DIR}' for the next attempt.")


def manage_videos_to_delete():
    print(f"Checking for videos to delete in '{VIDEOS_TO_DELETE_DIR}'...")
    VIDEOS_TO_DELETE_DIR.mkdir(parents=True, exist_ok=True)
        
    videos_to_remove = list(VIDEOS_TO_DELETE_DIR.glob("*.mp4"))
    if not videos_to_remove:
        print("No videos found in to_delete directory.")
        return

    for video in videos_to_remove:
        print(f"Deleting processed video: '{video.name}'")
        try:
            video.unlink()
            print(f"Successfully deleted '{video.name}'.")
        except Exception as e:
            print(f"ERROR: Could not delete video '{video.name}': {e}")

# --- Main Execution ---
if __name__ == "__main__":
    # Default video metadata (can be overridden or made more dynamic)
    today_str = datetime.today().strftime("%Y-%m-%d")
    default_title = f"Cinema short {today_str}" # Use {filename} or {date} placeholders
    default_description = "A short video about Cinema. Uploaded on {date}. Video: {filename}. Enjoy!"
    default_category = "22"  # Category for "People & Blogs" or choose appropriately
    default_keywords = "cinema,short,movie"
    default_privacy_status = "public" # Or "private", "unlisted"

    # --- Argument Parsing (Optional - for overriding defaults if run manually) ---
    parser = argparse.ArgumentParser(description="Uploads videos to YouTube non-interactively.")
    parser.add_argument("--title", default=default_title, help="Video title template. Can use {filename} and {date}.")
    parser.add_argument("--description", default=default_description, help="Video description template. Can use {filename} and {date}.")
    parser.add_argument("--category", default=default_category, help="Numeric video category.")
    parser.add_argument("--keywords", default=default_keywords, help="Video keywords, comma-separated.")
    parser.add_argument("--privacyStatus", choices=VALID_PRIVACY_STATUSES, default=default_privacy_status, help="Video privacy status.")
    cli_args = parser.parse_args()

    print("Starting YouTube upload process...")
    
    # Ensure data directories exist
    VIDEOS_TO_POST_DIR.mkdir(parents=True, exist_ok=True)
    VIDEOS_TO_DELETE_DIR.mkdir(parents=True, exist_ok=True)

    # File-based lock to prevent multiple instances from running concurrently
    lock = FileLock(str(LOCK_FILE_PATH), timeout=1) # Timeout of 1 second to acquire lock

    try:
        with lock:
            print(f"Lock acquired: {LOCK_FILE_PATH}")
            youtube_service = get_authenticated_service()
            
            print("--- Managing videos to share ---")
            manage_videos_to_share(youtube_service,
                                   cli_args.title,
                                   cli_args.description,
                                   cli_args.category,
                                   cli_args.keywords,
                                   cli_args.privacyStatus)
            
            print("\n--- Managing videos to delete ---")
            manage_videos_to_delete()
            
            print("\nProcess completed.")
    except Timeout:
        print(f"Could not acquire lock on '{LOCK_FILE_PATH}'. Another instance may be running. Skipping this run.")
    except Exception as e:
        print(f"An unexpected error occurred in the main process: {e}")
        # Consider more specific error handling or logging here
    finally:
        if lock.is_locked:
            lock.release()
            print(f"Lock released: {LOCK_FILE_PATH}")











# import sys
# from pathlib import Path
# import shutil

# import http.client as httplib
# import httplib2
# import os
# import random
# import sys
# import time
# from datetime import datetime
# from filelock import FileLock, Timeout

# import argparse
# # from apiclient.discovery import build
# # from apiclient.errors import HttpError
# # from apiclient.http import MediaFileUpload
# from oauth2client.client import flow_from_clientsecrets
# from oauth2client.file import Storage
# from oauth2client.tools import argparser, run_flow
# from google_auth_oauthlib.flow import InstalledAppFlow
# from google.auth.transport.requests import Request
# from google.oauth2.credentials import Credentials
# from httplib2 import Http


# # Explicitly tell the underlying HTTP transport library not to retry, since
# # we are handling retry logic ourselves.
# httplib2.RETRIES = 1

# # Maximum number of times to retry before giving up.
# MAX_RETRIES = 10

# # Always retry when these exceptions are raised.
# RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, httplib.NotConnected,
#   httplib.IncompleteRead, httplib.ImproperConnectionState,
#   httplib.CannotSendRequest, httplib.CannotSendHeader,
#   httplib.ResponseNotReady, httplib.BadStatusLine)

# # Always retry when an apiclient.errors.HttpError with one of these status
# # codes is raised.
# RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

# # The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# # the OAuth 2.0 information for this application, including its client_id and
# # client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# # the Google API Console at
# # https://console.cloud.google.com/.
# # Please ensure that you have enabled the YouTube Data API for your project.
# # For more information about using OAuth2 to access the YouTube Data API, see:
# #   https://developers.google.com/youtube/v3/guides/authentication
# # For more information about the client_secrets.json file format, see:
# #   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
# # CLIENT_SECRETS_FILE = "client_secret.json"
# CLIENT_SECRETS_FILE = os.getenv("CLIENT_SECRETS_FILE", "../client_secret.json")
# DATA_DIR = "/app/data"
# DATA_DIR = Path(DATA_DIR)

# # This OAuth 2.0 access scope allows an application to upload files to the
# # authenticated user's YouTube channel, but doesn't allow other types of access.
# YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
# YOUTUBE_API_SERVICE_NAME = "youtube"
# YOUTUBE_API_VERSION = "v3"

# # This variable defines a message to display if the CLIENT_SECRETS_FILE is
# # missing.
# MISSING_CLIENT_SECRETS_MESSAGE = """
# WARNING: Please configure OAuth 2.0

# To make this sample run you will need to populate the client_secrets.json file
# found at:

#    %s

# with information from the API Console
# https://console.cloud.google.com/

# For more information about the client_secrets.json file format, please visit:
# https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
# """ % os.path.abspath(os.path.join(os.path.dirname(__file__),
#                                    CLIENT_SECRETS_FILE))

# VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

# SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# path_root = Path(__file__).parent.parent
# # path_data = path_root /"app"/ "data"
# path_data = path_root / "results"


# # OLD VERSION
# # def get_authenticated_service(args):
# #   flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
# #     scope=YOUTUBE_UPLOAD_SCOPE,
# #     message=MISSING_CLIENT_SECRETS_MESSAGE)

# #   storage = Storage("%s-oauth2.json" % sys.argv[0])
# #   #   storage = Storage('oauth2.json') 
# #   credentials = storage.get()

# #   if credentials is None or credentials.invalid:
# #     credentials = run_flow(flow, storage, args)

# #   return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
# #     http=credentials.authorize(httplib2.Http()))

# def get_authenticated_service(args):
#     flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
#                                    scope=YOUTUBE_UPLOAD_SCOPE,
#                                    message=MISSING_CLIENT_SECRETS_MESSAGE)
    
#     storage = Storage("%s-oauth2.json" % sys.argv[0])
#     credentials = storage.get()

#     # Vérifie si les credentials sont invalides ou expirés
#     if credentials is None or credentials.invalid:
#         try:
#             if credentials and credentials.expired and credentials.refresh_token:
#                 # Essaie de rafraîchir les credentials avec le refresh_token
#                 credentials.refresh(Http())
#             else:
#                 # Si le refresh échoue ou il n'y a pas de refresh_token, relance le flow OAuth2
#                 print("Le token est invalide ou expiré. Relance le flow OAuth2...")
#                 os.remove("%s-oauth2.json" % sys.argv[0])  # Supprime le token pour en générer un nouveau
#                 credentials = run_flow(flow, storage, args)  # Demande une nouvelle autorisation

#         except Exception as e:
#             print(f"Erreur lors du rafraîchissement du token ou du flow OAuth2: {e}")
#             raise

#     return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
#                  http=credentials.authorize(Http()))

# # def get_authenticated_service(args):
# #     creds = None
# #     token_file = f"{sys.argv[0]}-token.json"

# #     if os.path.exists(token_file):
# #         creds = Credentials.from_authorized_user_file(token_file, SCOPES)

# #     if not creds or not creds.valid:
# #         if creds and creds.expired and creds.refresh_token:
# #             try:
# #                 creds.refresh(Request())
# #             except Exception as e:
# #                 print(f"Could not refresh token: {e}")
# #         else:
# #             flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
# #             creds = flow.run_local_server(port=8081, open_browser=False)

# #         # Save the credentials for next run
# #         with open(token_file, 'w') as token:
# #             token.write(creds.to_json())

# #     return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=creds)

# def initialize_upload(youtube, options):
#   tags = None
#   if options.keywords:
#     tags = options.keywords.split(",")

#   body=dict(
#     snippet=dict(
#       title=options.title,
#       description=options.description,
#       tags=tags,
#       categoryId=options.category
#     ),
#     status=dict(
#       privacyStatus=options.privacyStatus
#     )
#   )

#   print('inserting video')

#   # Call the API's videos.insert method to create and upload the video.
#   insert_request = youtube.videos().insert(
#     part=",".join(body.keys()),
#     body=body,
#     # The chunksize parameter specifies the size of each chunk of data, in
#     # bytes, that will be uploaded at a time. Set a higher value for
#     # reliable connections as fewer chunks lead to faster uploads. Set a lower
#     # value for better recovery on less reliable connections.
#     #
#     # Setting "chunksize" equal to -1 in the code below means that the entire
#     # file will be uploaded in a single HTTP request. (If the upload fails,
#     # it will still be retried where it left off.) This is usually a best
#     # practice, but if you're using Python older than 2.6 or if you're
#     # running on App Engine, you should set the chunksize to something like
#     # 1024 * 1024 (1 megabyte).
#     media_body=MediaFileUpload(options.file, chunksize=-1, resumable=True)
#   )

#   print('resumable_upload')
#   resumable_upload(insert_request)

# # This method implements an exponential backoff strategy to resume a
# # failed upload.
# def resumable_upload(insert_request):
#   response = None
#   error = None
#   retry = 0
#   while response is None:
#     try:
#       print("Uploading file...")
#       status, response = insert_request.next_chunk()
#       if response is not None:
#         if 'id' in response:
#           print( "Video id '%s' was successfully uploaded." % response['id'])
#         else:
#           exit("The upload failed with an unexpected response: %s" % response)
#     except HttpError as e:
#       if e.resp.status in RETRIABLE_STATUS_CODES:
#         error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status,
#                                                              e.content)
#       else:
#         raise
#     except RETRIABLE_EXCEPTIONS as e:
#       error = "A retriable error occurred: %s" % e

#     if error is not None:
#       print(error)
#       retry += 1
#       if retry > MAX_RETRIES:
#         exit("No longer attempting to retry.")

#       max_sleep = 2 ** retry
#       sleep_seconds = random.random() * max_sleep
#       print("Sleeping %f seconds and then retrying...") % sleep_seconds
#       time.sleep(sleep_seconds)

# def upload_video_youtube(one_video_path, 
#                          title,
#                          description,
#                          category,
#                          keywords,
#                          privacyStatus):
#     #   argparser.add_argument("--file", required=True, help="Video file to upload")
#     #   argparser.add_argument("--title", help="Video title", default="Test Title")
#     #   argparser.add_argument("--description", help="Video description",
#     #     default="Test Description")
#     #   argparser.add_argument("--category", default="22",
#     #     help="Numeric video category. " +
#     #       "See https://developers.google.com/youtube/v3/docs/videoCategories/list")
#     #   argparser.add_argument("--keywords", help="Video keywords, comma separated",
#     #     default="")
#     #   argparser.add_argument("--privacyStatus", choices=VALID_PRIVACY_STATUSES,
#     #     default=VALID_PRIVACY_STATUSES[0], help="Video privacy status.")
#     #   args = argparser.parse_args()
    
#     print(f"Uploading {one_video_path.name}")
#     # check if privacyStatus is valid
#     assert privacyStatus in VALID_PRIVACY_STATUSES, f"privacyStatus must be in {VALID_PRIVACY_STATUSES}"

#     dict_args = {
#         "file": one_video_path,
#         "title": title,
#         "description": description,
#         "category": category,
#         "keywords": keywords,
#         "privacyStatus": privacyStatus,
#         "logging_level" : 'INFO'
#     }

#     args = argparse.Namespace()
#     args.logging_level = dict_args['logging_level']
#     args.file = dict_args['file']
#     args.title = dict_args['title']
#     args.description = dict_args['description']
#     args.category = dict_args['category']
#     args.keywords = dict_args['keywords']
#     args.privacyStatus = dict_args['privacyStatus']
#     args.noauth_local_webserver = False
#     args.auth_host_port = [8080]  # Port local pour le serveur d'authentification OAuth
#     args.auth_host_name = 'localhost'  # Nom d'hôte local pour OAuth
#     args.noauth_local_webserver = False  # Paramètre pour désactiver le serveur local

#     if not os.path.exists(dict_args['file']):
#         exit("Please specify a valid file using the --file= parameter.")

#     youtube = get_authenticated_service(args)
#     print("Authenticated")
#     try:
#         initialize_upload(youtube, args)
#     except HttpError as e:
#         print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))


# def manage_videos_to_share(title, description, category, keywords, privacyStatus):
#     # post one video to youtube then move the video from data/to_share to data/to_delete
#     print("Share videos")
#     to_share_path = path_data / "to_post"
#     to_delete_path = path_data / "to_delete"
        
#     list_videos_path = list(to_share_path.glob("*.mp4"))
#     if len(list_videos_path) == 0:
#         pass
#     else:
#         one_video_path = list_videos_path[0]
#         upload_video_youtube(one_video_path, 
#                              title,
#                              description,
#                              category,
#                              keywords,
#                              privacyStatus)
#         print('Uploading video')
#         shutil.move(one_video_path, to_delete_path / one_video_path.name)

# def manage_videos_to_delete():
#     print("Delete videos")
#     print(path_data)
#     print(path_root)
#     print(path_data / "to_delete")
#     to_delete_path = path_data / "to_delete"
#     print(list(to_delete_path.glob("*.mp4")))
#     for video in to_delete_path.glob("*.mp4"):
#         # delete the videos
#         print(f"Deleting {video.name}")
#         video.unlink()

# if __name__ == "__main__":
#     # get date from today
#     today = datetime.today().strftime("%Y-%m-%d")
#     title = f"Cinema short {today}"
#     description = "A short video about Cinema. Enjoy!"
#     category = "22"
#     keywords = "cinema, short, movie"
#     privacyStatus = "public"

#     lock_path = "/tmp/youtube_upload.lock"
#     lock = FileLock(lock_path, timeout=1)
#     try:
#         with lock:
#           print('manage_videos_to_share')
#           manage_videos_to_share(title, description, category, keywords, privacyStatus)
#           print('manage_videos_to_delete')
#           manage_videos_to_delete()
#     except Timeout:
#       print("Another upload is in progress, skipping this run.")