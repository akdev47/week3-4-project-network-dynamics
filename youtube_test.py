from googleapiclient.discovery import build
from dotenv import load_dotenv
import os

# Load secret keys from .env file
load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")

if API_KEY is None:
    raise ValueError("API key not found! Did you create a .env file?")

youtube = build("youtube", "v3", developerKey=API_KEY)

request = youtube.search().list(
    part="snippet",
    q="lofi hip hop",
    maxResults=5,
    type="video"
)
response = request.execute()

for item in response["items"]:
    print(item["snippet"]["title"])
