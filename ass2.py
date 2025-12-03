"""
Assignment 2 – Network Effects (Chapter 17)
-------------------------------------------

This script:
- Reads the youtube_top100.zip dataset (date-labelled JSON files)
- Builds a time series of view counts for a small set of songs
- Produces a labelled plot "View count over time" for Section 2 of the report

Figures from this file are used in:
- Report Section 2, Question 2(a), (b), (c)
"""

import os
import json
import zipfile
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt

# === CONFIGURATION ========================================================= #

# Path to the ZIP file relative to the project root
YOUTUBE_ZIP_PATH = os.path.join("data", "youtube_top100.zip")

# OPTIONAL: if you want to fix the songs yourself, put titles here.
# If this list is empty, the script will automatically pick the top_k
# most-viewed songs on the first day.
MANUAL_TITLES = [
    # "Adele - Hello",
    # "Mark Ronson - Uptown Funk ft. Bruno Mars",
]

TOP_K_AUTOMATIC = 3  # how many songs to track if MANUAL_TITLES is empty


# === HELPER FUNCTIONS ====================================================== #

def parse_date_from_filename(name: str) -> datetime.date:
    """
    Filenames look like: 'youtube_top100/20151109_1800_data.json'
    We extract the '20151109' part and turn it into a date.
    """
    base = os.path.basename(name)              # '20151109_1800_data.json'
    date_str = base.split("_", 1)[0]           # '20151109'
    return datetime.strptime(date_str, "%Y%m%d").date()


def choose_target_titles(z: zipfile.ZipFile, json_names):
    """
    Decide which song titles to track.
    - If MANUAL_TITLES is non-empty, we use those.
    - Otherwise, we pick TOP_K_AUTOMATIC songs with highest viewCount on
      the first day.
    """
    if MANUAL_TITLES:
        print("Using manually specified titles.")
        return MANUAL_TITLES

    first_name = sorted(json_names)[0]
    with z.open(first_name) as f:
        first_day_data = json.load(f)

    pairs = [
        (item["snippet"]["title"], int(item["statistics"]["viewCount"]))
        for item in first_day_data
    ]
    pairs.sort(key=lambda x: -x[1])  # sort by viewCount descending
    titles = [title for title, _ in pairs[:TOP_K_AUTOMATIC]]

    print("Automatically selected titles (top by view count on first day):")
    for t in titles:
        print("  -", t)

    return titles


def load_view_time_series(zip_path: str):
    """
    Load (date, title, views) rows for the selected songs from the ZIP file.
    Returns a pandas DataFrame with columns ['date', 'title', 'views']
    and the list of tracked titles.
    """
    z = zipfile.ZipFile(zip_path)
    json_names = [n for n in z.namelist() if n.endswith(".json")]

    target_titles = choose_target_titles(z, json_names)

    rows = []

    for name in sorted(json_names):
        date = parse_date_from_filename(name)
        with z.open(name) as f:
            day_data = json.load(f)

        for item in day_data:
            title = item["snippet"]["title"]
            if title in target_titles:
                views = int(item["statistics"]["viewCount"])
                rows.append({"date": date, "title": title, "views": views})

    df = pd.DataFrame(rows)
    return df, target_titles


def plot_views_over_time(df: pd.DataFrame, output_path: str | None = None):
    """
    Create the main plot for Assignment 2:
    View count over time for selected songs.
    """
    # Pivot so each song is a column, index is date
    pivot = df.pivot(index="date", columns="title", values="views").sort_index()

    plt.figure(figsize=(10, 6))

    for title in pivot.columns:
        plt.plot(
            pivot.index,
            pivot[title],
            marker=".",
            linewidth=1.0,
            label=title,
        )

    plt.xlabel("Date")
    plt.ylabel("Cumulative view count")
    plt.title("View count over time for selected YouTube songs")
    plt.legend()
    plt.grid(True, linestyle="--", linewidth=0.5)
    plt.tight_layout()

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300)
        print(f"Saved figure to: {output_path}")
    else:
        plt.show()


# === MAIN ================================================================== #

def main():
    if not os.path.exists(YOUTUBE_ZIP_PATH):
        raise FileNotFoundError(
            f"Could not find {YOUTUBE_ZIP_PATH}. "
            "Make sure youtube_top100.zip is in the data/ folder."
        )

    df, titles = load_view_time_series(YOUTUBE_ZIP_PATH)
    print(f"Loaded {len(df)} rows for {len(titles)} songs.")
    print("Songs in this plot:")
    for t in titles:
        print("  -", t)

    # This image can be referenced as "Figure 2.1" in your report
    plot_views_over_time(df, output_path=os.path.join("figures", "a2_views_over_time.png"))


if __name__ == "__main__":
    main()
