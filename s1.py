"""
Assignment 1 – Cascading Effects (Web Science, Weeks 3–4)

This script does:

1a) Load the YouTube top-100 dataset and plot (likes - dislikes)
    over time for a few long-lived songs.

1b) Load the radio datasets (3FM megahit and Radio 538 alarmschijf)
    and plot the same metric for the songs that were NOT in Spotify top-100.

It reads JSON files directly from ZIP archives, so you do NOT need
to unzip anything.

Expected layout:

week3-4-project-network-dynamics/
  s1.py
  data/
    youtube_top100.zip
    radio3fm_megahit.zip
    radio538_alarmschijf.zip
"""

import os
import json
from datetime import datetime
import zipfile

import pandas as pd
import matplotlib.pyplot as plt


# ==========================
#  Helper: load from ZIP
# ==========================

def load_youtube_from_zip(zip_path: str) -> pd.DataFrame:
    """
    Load YouTube JSON snapshots from a ZIP file.

    Works for:
    - data/youtube_top100.zip
    - data/radio3fm_megahit.zip
    - data/radio538_alarmschijf.zip

    Returns DataFrame with columns:
      date, video_id, title, likes, dislikes, diff
    """
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"ZIP file not found: {zip_path}")

    rows = []

    print(f"[DEBUG] Opening ZIP: {zip_path}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        # all JSON members
        json_files = [name for name in zf.namelist() if name.lower().endswith(".json")]
        print(f"[DEBUG]  found {len(json_files)} JSON files in ZIP")
        if json_files:
            print("[DEBUG]  first few entries:")
            for name in json_files[:5]:
                print(f"         {name}")

        if not json_files:
            raise FileNotFoundError(f"No JSON files inside ZIP: {zip_path}")

        for name in json_files:
            filename = os.path.basename(name)

            # Try to extract a date from the filename, e.g. 20151109_1800_data.json
            date_part = filename.split("_")[0]
            if date_part.isdigit() and len(date_part) == 8:
                try:
                    date = datetime.strptime(date_part, "%Y%m%d").date()
                except ValueError:
                    # fallback: ignore date parsing problems
                    date = None
            else:
                date = None

            # Open and parse JSON
            with zf.open(name) as f:
                # bytes -> text
                data = json.load(f)

            if not isinstance(data, list):
                raise TypeError(f"Expected list at top level in {name}, got {type(data)}")

            for item in data:
                # ---- video_id extraction ----
                raw_id = item.get("id")
                if isinstance(raw_id, dict) and "videoId" in raw_id:
                    video_id = raw_id["videoId"]
                elif "resourceId" in item and isinstance(item["resourceId"], dict) and "videoId" in item["resourceId"]:
                    video_id = item["resourceId"]["videoId"]
                else:
                    video_id = raw_id  # fallback

                snippet = item.get("snippet", {})
                title = snippet.get("title", "Unknown title")

                stats = item.get("statistics", {})
                likes = int(stats.get("likeCount", 0))
                dislikes = int(stats.get("dislikeCount", 0))

                rows.append(
                    {
                        "date": date,
                        "video_id": video_id,
                        "title": title,
                        "likes": likes,
                        "dislikes": dislikes,
                        "diff": likes - dislikes,
                    }
                )

    df = pd.DataFrame(rows)
    print(f"[DEBUG] DataFrame from {os.path.basename(zip_path)}: shape={df.shape}")
    print(f"[DEBUG] Columns: {list(df.columns)}")
    return df


def pick_long_lived_songs(df: pd.DataFrame, min_days: int, max_songs: int):
    """
    Select video_ids that appear in the dataset at least `min_days` times
    (on different dates). Limit to at most `max_songs` IDs.
    """
    # If dates are None (couldn't parse), treat them as one "date"
    if df["date"].isna().all():
        # no meaningful dates; just count occurrences
        counts = df.groupby("video_id")["title"].count().sort_values(ascending=False)
    else:
        counts = (
            df.dropna(subset=["date"])
              .groupby("video_id")["date"]
              .nunique()
              .sort_values(ascending=False)
        )

    selected_ids = counts[counts >= min_days].index[:max_songs]
    return list(selected_ids)


def plot_diff_over_time(df: pd.DataFrame, video_ids, title_prefix: str):
    """
    Plot (likes - dislikes) over time for the given list of video_ids.

    Each song becomes one line in the plot.
    """
    plt.figure()
    for vid in video_ids:
        sub = df[df["video_id"] == vid].copy()
        # if we have dates, sort by date
        if "date" in sub.columns and not sub["date"].isna().all():
            sub = sub.sort_values("date")
            x = sub["date"]
        else:
            # fallback: just use index
            x = range(len(sub))

        if sub.empty:
            continue

        label = sub["title"].iloc[0]
        if len(label) > 40:
            label = label[:37] + "..."
        plt.plot(x, sub["diff"], marker="o", label=label)

    plt.xlabel("Date" if "date" in df.columns and not df["date"].isna().all() else "Observation index")
    plt.ylabel("Likes − Dislikes")
    plt.title(f"{title_prefix} – evolution of likes − dislikes")
    plt.legend()
    plt.tight_layout()
    plt.show()


# ==========================
#  Assignment 1a
# ==========================

def run_assignment_1a():
    """
    1a) Plot difference over time between likes and dislikes of songs in YouTube top-100.
    """
    yt_zip = os.path.join("data", "youtube_top100.zip")
    print(f"Loading YouTube top-100 from ZIP: {yt_zip}")
    df_yt = load_youtube_from_zip(yt_zip)

    # Filter out rows where video_id is missing
    df_yt = df_yt[df_yt["video_id"].notna()]
    print(f"After dropping missing video_id: {len(df_yt)} rows, {df_yt['video_id'].nunique()} unique videos.")

    # Songs that appear on many different dates in the top-100
    long_ids = pick_long_lived_songs(df_yt, min_days=40, max_songs=5)
    if not long_ids:
        print("[WARN] No songs found with >= 40 distinct dates; lowering threshold to 10.")
        long_ids = pick_long_lived_songs(df_yt, min_days=10, max_songs=5)

    print("Selected video IDs for plotting (1a):")
    for vid in long_ids:
        title = df_yt[df_yt["video_id"] == vid]["title"].iloc[0]
        print(f"  {vid} – {title}")

    plot_diff_over_time(df_yt, long_ids, title_prefix="YouTube Top-100")


# ==========================
#  Assignment 1b
# ==========================

def run_assignment_1b():
    """
    1b) Plot difference over time between likes and dislikes of megahit
        and alarmschijf songs (not in Spotify top-100 at the time).
    """
    radio_zips = [
        (os.path.join("data", "radio3fm_megahit.zip"), "3FM Megahit"),
        (os.path.join("data", "radio538_alarmschijf.zip"), "Radio 538 Alarmschijf"),
    ]

    for zip_path, nice_name in radio_zips:
        print(f"\nLoading {nice_name} from ZIP: {zip_path}")
        df_radio = load_youtube_from_zip(zip_path)

        df_radio = df_radio[df_radio["video_id"].notna()]
        print(f"  After dropping missing video_id: {len(df_radio)} rows, {df_radio['video_id'].nunique()} unique videos.")

        # These are tracked for only ~2 weeks → lower min_days
        long_ids = pick_long_lived_songs(df_radio, min_days=5, max_songs=5)
        if not long_ids:
            print(f"  [WARN] No songs found with >= 5 distinct dates for {nice_name}; lowering threshold to 2.")
            long_ids = pick_long_lived_songs(df_radio, min_days=2, max_songs=5)

        print(f"  Selected video IDs for plotting ({nice_name}):")
        for vid in long_ids:
            title = df_radio[df_radio["video_id"] == vid]["title"].iloc[0]
            print(f"    {vid} – {title}")

        plot_diff_over_time(df_radio, long_ids, title_prefix=nice_name)


# ==========================
#  Main
# ==========================

if __name__ == "__main__":
    run_assignment_1a()
    run_assignment_1b()
