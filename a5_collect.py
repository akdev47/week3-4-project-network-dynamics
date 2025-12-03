"""
Assignment 5(a) – Collect your own YouTube dataset (hip hop)
------------------------------------------------------------

This script uses the YouTube Data API to collect at least 200 short
music (category 10) videos related to hip hop and saves them as JSON.

Figures / data from this script are used in:
- Report Section 5(a)
"""

import os
import json
from datetime import datetime

from dotenv import load_dotenv
from googleapiclient.discovery import build

# ================== CONFIGURATION ==================================== #

# Search query focused on hip hop
SEARCH_QUERY = "hip hop music"

# Only short music videos, as required in the assignment
VIDEO_CATEGORY_ID = "10"      # 10 = Music
VIDEO_DURATION = "short"      # 'short' = < 4 minutes

# How many videos we aim to collect in total (minimum 200)
TARGET_VIDEO_COUNT = 200

# Output path for the dataset
OUTPUT_PATH = os.path.join("data", "my_hiphop_youtube_dataset.json")

# ===================================================================== #

def get_youtube_client():
    """
    Build the YouTube API client using an API key stored in .env.

    .env must contain:
        YOUTUBE_API_KEY=your_real_key_here
    """
    load_dotenv()
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise RuntimeError("YOUTUBE_API_KEY not found in environment (.env file).")
    return build("youtube", "v3", developerKey=api_key)


def search_video_ids(youtube):
    """
    Use youtube.search().list to collect video IDs matching the query.

    Returns a list of unique video IDs (strings).
    """
    video_ids = []
    seen_ids = set()
    page_token = None

    while len(video_ids) < TARGET_VIDEO_COUNT:
        request = youtube.search().list(
            part="id",
            q=SEARCH_QUERY,
            type="video",
            videoCategoryId=VIDEO_CATEGORY_ID,
            videoDuration=VIDEO_DURATION,
            maxResults=50,
            pageToken=page_token,
        )
        response = request.execute()

        for item in response.get("items", []):
            vid = item["id"]["videoId"]
            if vid not in seen_ids:
                seen_ids.add(vid)
                video_ids.append(vid)

        page_token = response.get("nextPageToken")
        if not page_token:
            # No more pages – stop even if we didn't reach TARGET_VIDEO_COUNT
            break

        print(f"Collected {len(video_ids)} video IDs so far...")

    print(f"Total unique video IDs collected: {len(video_ids)}")
    return video_ids


def fetch_video_details(youtube, video_ids):
    """
    Given a list of video IDs, fetch snippet + statistics for each video.

    Returns a list of simplified dicts containing only the fields we need.
    """
    videos = []

    # YouTube API allows up to 50 IDs per videos().list call
    for i in range(0, len(video_ids), 50):
        batch_ids = video_ids[i:i + 50]
        request = youtube.videos().list(
            part="snippet,statistics",
            id=",".join(batch_ids),
            maxResults=50,
        )
        response = request.execute()

        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            videos.append({
                "id": item.get("id"),
                "title": snippet.get("title"),
                "channelId": snippet.get("channelId"),
                "channelTitle": snippet.get("channelTitle"),
                "publishedAt": snippet.get("publishedAt"),
                "viewCount": int(stats.get("viewCount", 0)),
                "likeCount": int(stats.get("likeCount", 0)) if "likeCount" in stats else None,
                "commentCount": int(stats.get("commentCount", 0)) if "commentCount" in stats else None,
            })

    print(f"Fetched details for {len(videos)} videos.")
    return videos


def save_dataset(videos):
    """
    Save the collected dataset as JSON.
    """
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    dataset = {
        "query": SEARCH_QUERY,
        "videoCategoryId": VIDEO_CATEGORY_ID,
        "videoDuration": VIDEO_DURATION,
        "collectedAt": datetime.utcnow().isoformat() + "Z",
        "videoCount": len(videos),
        "items": videos,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"Saved dataset with {len(videos)} videos to {OUTPUT_PATH}")


def main():
    youtube = get_youtube_client()

    video_ids = search_video_ids(youtube)
    videos = fetch_video_details(youtube, video_ids)
    save_dataset(videos)


if __name__ == "__main__":
    main()
