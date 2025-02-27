import os
import time
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv
import logging

def load_env():
    load_dotenv()
    return {
        "API_KEY": os.getenv("API_KEY"),
        "CLIENT_ID": os.getenv("CLIENT_ID"),
        "CLIENT_SECRET": os.getenv("CLIENT_SECRET"),
        "ACCESS_TOKEN": os.getenv("ACCESS_TOKEN"),
        "REFRESH_TOKEN": os.getenv("REFRESH_TOKEN"),
    }

def get_youtube_service():
    credentials = load_env()
    return build("youtube", "v3", developerKey=credentials["API_KEY"])

def upload_video(video_path):
    youtube = get_youtube_service()
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": os.path.basename(video_path),
                "description": "Uploaded using API",
                "tags": ["test", "upload"],
                "categoryId": "22"
            },
            "status": {"privacyStatus": "public"}
        },
        media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True)
    )
    response = request.execute()
    logging.info(f"Uploaded {video_path}: {response}")

def process_videos():
    folder = "to_share"
    if not os.path.exists(folder):
        logging.info("No folder to process")
        return
    
    for file in os.listdir(folder):
        if file.endswith(".mp4"):
            upload_video(os.path.join(folder, file))
            os.remove(os.path.join(folder, file))

def clean_to_delete():
    folder = "to_delete"
    if not os.path.exists(folder):
        logging.info("No folder to clean")
        return
    
    for file in os.listdir(folder):
        file_path = os.path.join(folder, file)
        os.remove(file_path)
        logging.info(f"Deleted {file_path}")

if __name__ == "__main__":
    process_videos()
    clean_to_delete()