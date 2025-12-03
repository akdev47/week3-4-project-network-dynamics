"""
s3.py – Assignment 3: Rich-Get-Richer (Popularity) Effects

This script does the following:

3a) For several days, plots the distribution of YouTube view counts
    among all songs (rank vs views) in linear and log-log scales.

3b) (Theory, no code): exponential growth argument – write in report.

3c) (Uses plots from Assignment 2; optional helper here if needed).

3d) Compares rankings of songs in Spotify (top-100 position) with
    rankings in YouTube (by view count) for several days.

Datasets expected:
  data/youtube_top100.zip
  data/spotify_top100.zip
"""

import os
import json
import math
import zipfile
from datetime import datetime
from typing import List, Dict, Tuple, Iterable

import matplotlib.pyplot as plt


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

DATA_DIR = "data"
YOUTUBE_ZIP = os.path.join(DATA_DIR, "youtube_top100.zip")
SPOTIFY_ZIP = os.path.join(DATA_DIR, "spotify_top100.zip")
PLOTS_DIR = "plots"


# ---------------------------------------------------------------------
# Helpers: general
# ---------------------------------------------------------------------

def ensure_dir(path: str) -> None:
    """Create directory if it doesn't exist."""
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)


def evenly_spaced_indices(n: int, k: int) -> List[int]:
    """
    Pick k indices evenly spaced from range(0, n).
    Assumes k <= n and k >= 1.
    """
    if k == 1:
        return [0]
    return [round(i * (n - 1) / (k - 1)) for i in range(k)]


def clear_plots(prefix: str) -> None:
    """
    Delete old plot files in PLOTS_DIR whose filename starts with prefix.
    Example prefixes: 's3a_', 's3d_'.
    """
    if not os.path.isdir(PLOTS_DIR):
        return
    for fname in os.listdir(PLOTS_DIR):
        if fname.startswith(prefix) and fname.endswith(".png"):
            try:
                os.remove(os.path.join(PLOTS_DIR, fname))
            except OSError:
                pass


# ---------------------------------------------------------------------
# Helpers: YouTube data
# ---------------------------------------------------------------------

def iter_youtube_days(zip_path: str) -> Iterable[Tuple[datetime, List[dict]]]:
    """
    Iterate over all days in the YouTube dataset.

    Yields:
        (date, videos)
    where
        date   = datetime.date object
        videos = list of video dicts for that day
    """
    with zipfile.ZipFile(zip_path, "r") as z:
        json_files = sorted(
            name for name in z.namelist() if name.endswith(".json")
        )

        for name in json_files:
            base = os.path.basename(name)  # e.g. 20151109_1800_data.json
            date_str = base.split("_")[0]  # '20151109'
            date = datetime.strptime(date_str, "%Y%m%d").date()

            data = json.loads(z.read(name).decode("utf-8"))
            # data is a list of 100 YouTube video objects
            yield date, data


def get_youtube_view_counts_for_day(videos: List[dict]) -> List[int]:
    """Return list of view counts for one day from YouTube daily data."""
    views = []
    for v in videos:
        stats = v.get("statistics", {})
        vc = stats.get("viewCount")
        if vc is not None:
            try:
                views.append(int(vc))
            except ValueError:
                # Just skip malformed entries
                continue
    return views


# ---------------------------------------------------------------------
# Helpers: Spotify data
# ---------------------------------------------------------------------

def _spotify_json_files(zip_path: str) -> List[str]:
    """Return sorted list of Spotify JSON filenames inside the zip."""
    with zipfile.ZipFile(zip_path, "r") as z:
        all_json = [n for n in z.namelist() if n.endswith(".json")]
    return sorted(all_json)


def _pick_spotify_file_for_date(files: List[str], date_str: str) -> str:
    """
    For a given date string 'YYYYMMDD', choose the most appropriate Spotify file.

    The zip sometimes has multiple files for the same date (e.g., 1328 and 1800).
    We prefer the one containing '1800' in the filename if it exists,
    otherwise we take the first matching file.
    """
    candidates = [f for f in files if date_str in os.path.basename(f)]
    if not candidates:
        raise FileNotFoundError(f"No Spotify JSON for date {date_str}")
    for c in candidates:
        if "_1800_" in c:
            return c
    # Fallback: just the first
    return sorted(candidates)[0]


def iter_spotify_days(zip_path: str) -> Iterable[Tuple[datetime, List[dict]]]:
    """
    Iterate over all days in the Spotify dataset.

    Yields:
        (date, tracks)
    where
        date   = datetime.date object
        tracks = list of track-info dicts:
                 {
                   'id': str,
                   'name': str,
                   'artists': str,
                   'position': int  (1..100)
                 }
    """
    files = _spotify_json_files(zip_path)
    with zipfile.ZipFile(zip_path, "r") as z:
        # Get all unique dates present in the filenames
        dates = sorted(
            sorted({
                os.path.basename(f).split("_")[0]  # '20151109'
                for f in files
            })
        )

        for date_str in dates:
            # Try to align with YouTube time (prefer *_1800_ if present)
            fname = _pick_spotify_file_for_date(files, date_str)
            payload = json.loads(z.read(fname).decode("utf-8"))
            items = payload["tracks"]["items"]

            date = datetime.strptime(date_str, "%Y%m%d").date()
            tracks = []
            for pos, item in enumerate(items, start=1):
                t = item["track"]
                artists = ", ".join(a["name"] for a in t["artists"])
                tracks.append(
                    {
                        "id": t["id"],
                        "name": t["name"],
                        "artists": artists,
                        "position": pos,
                    }
                )

            yield date, tracks


# ---------------------------------------------------------------------
# Part 3a – Distributions (rank vs view-count in linear/log-log)
# ---------------------------------------------------------------------

def plot_viewcount_distributions(num_days: int = 5) -> None:
    """
    For several days, plot the distribution of view counts among all
    songs (rank vs view count):

    - linear scale
    - log-log scale

    Saves plots into PLOTS_DIR.
    """
    ensure_dir(PLOTS_DIR)

    # clear old 3a plots so they don't multiply
    clear_plots("s3a_")

    yt_days = list(iter_youtube_days(YOUTUBE_ZIP))
    if not yt_days:
        print("No YouTube data found. Check your YOUTUBE_ZIP path.")
        return

    num_days = min(num_days, len(yt_days))
    indices = evenly_spaced_indices(len(yt_days), num_days)

    for idx in indices:
        date, videos = yt_days[idx]
        date_str = date.strftime("%Y%m%d")

        views = get_youtube_view_counts_for_day(videos)
        if not views:
            continue

        views_sorted = sorted(views, reverse=True)
        ranks = list(range(1, len(views_sorted) + 1))

        # --- Linear plot ---
        plt.figure()
        plt.plot(ranks, views_sorted, marker="o")
        plt.xlabel("Rank (1 = most viewed)")
        plt.ylabel("View count")
        plt.title(f"YouTube view distribution (linear) – {date}")
        plt.tight_layout()
        out_path = os.path.join(
            PLOTS_DIR, f"s3a_views_rank_linear_{date_str}.png"
        )
        plt.savefig(out_path, dpi=150)
        plt.close()

        # --- Log-log plot ---
        plt.figure()
        plt.loglog(ranks, views_sorted, marker="o", linestyle="none")
        plt.xlabel("Rank (log scale)")
        plt.ylabel("View count (log scale)")
        plt.title(f"YouTube view distribution (log-log) – {date}")
        plt.tight_layout()
        out_path = os.path.join(
            PLOTS_DIR, f"s3a_views_rank_loglog_{date_str}.png"
        )
        plt.savefig(out_path, dpi=150)
        plt.close()

        print(f"[3a] Saved plots for {date}.")


# ---------------------------------------------------------------------
# Part 3d – Compare Spotify rank vs YouTube rank
# ---------------------------------------------------------------------

def _build_spotify_youtube_mapping() -> Dict[str, str]:
    """
    Build a mapping from Spotify track ID -> YouTube video ID.

    We use a single reference day (the first one where both datasets
    are available) and match based on:
      - track name
      - artist names
    and the YouTube video title.

    Returns:
        dict: spotify_id -> youtube_video_id
    """
    # Grab first matching day that exists in BOTH zips
    yt_days = list(iter_youtube_days(YOUTUBE_ZIP))
    sp_days = list(iter_spotify_days(SPOTIFY_ZIP))

    yt_by_date = {d: vids for d, vids in yt_days}
    sp_by_date = {d: tracks for d, tracks in sp_days}
    common_dates = sorted(set(yt_by_date.keys()) & set(sp_by_date.keys()))
    if not common_dates:
        print("No overlapping dates between Spotify and YouTube datasets.")
        return {}

    ref_date = common_dates[0]
    print(f"Building Spotify–YouTube mapping using reference date {ref_date}")

    yt_videos = yt_by_date[ref_date]
    sp_tracks = sp_by_date[ref_date]

    mapping: Dict[str, str] = {}  # spotify_id -> youtube_id

    for t in sp_tracks:
        spotify_id = t["id"]
        track_name = t["name"].lower()
        artist_tokens = [a.strip().lower() for a in t["artists"].split(",")]

        best_yt_id = None

        # First pass: require both track name and at least one artist in title
        for v in yt_videos:
            title = v["snippet"]["title"].lower()
            if track_name in title and any(a in title for a in artist_tokens):
                best_yt_id = v["id"]
                break

        # Second pass: just track name
        if best_yt_id is None:
            for v in yt_videos:
                title = v["snippet"]["title"].lower()
                if track_name in title:
                    best_yt_id = v["id"]
                    break

        if best_yt_id is not None:
            mapping[spotify_id] = best_yt_id

    print(
        f"Mapped {len(mapping)} of {len(sp_tracks)} Spotify tracks "
        "to YouTube videos on the reference day."
    )
    return mapping


def _spearman_correlation(xs: List[float], ys: List[float]) -> float:
    """
    Compute Spearman (actually Pearson on ranks) correlation coefficient.
    xs and ys are already ranks in our case, so this is just Pearson.

    Returns:
        correlation in [-1, 1]
    """
    if len(xs) != len(ys) or len(xs) == 0:
        return float("nan")

    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n

    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))

    if den_x == 0 or den_y == 0:
        return float("nan")
    return num / (den_x * den_y)


def compare_spotify_youtube_rankings(num_days: int = 5) -> None:
    """
    For several days, compare Spotify ranking (top-100 position) with
    YouTube ranking (by view count) for songs that we can match in
    both datasets.

    For each day:
      - compute rank on Spotify (position 1..100)
      - compute rank on YouTube (sort viewCount descending)
      - compute correlation and save a scatter plot

    Plots are saved into PLOTS_DIR.
    """
    ensure_dir(PLOTS_DIR)

    # clear old 3d plots so they don't multiply
    clear_plots("s3d_")

    # Build mapping once (Spotify track ID -> YouTube video ID)
    mapping = _build_spotify_youtube_mapping()
    if not mapping:
        return

    yt_days = list(iter_youtube_days(YOUTUBE_ZIP))
    sp_days = list(iter_spotify_days(SPOTIFY_ZIP))

    yt_by_date = {d: vids for d, vids in yt_days}
    sp_by_date = {d: tracks for d, tracks in sp_days}
    common_dates = sorted(set(yt_by_date.keys()) & set(sp_by_date.keys()))
    if not common_dates:
        print("No overlapping dates between Spotify and YouTube datasets.")
        return

    num_days = min(num_days, len(common_dates))
    indices = evenly_spaced_indices(len(common_dates), num_days)
    selected_dates = [common_dates[i] for i in indices]

    for date in selected_dates:
        yt_videos = yt_by_date[date]
        sp_tracks = sp_by_date[date]
        date_str = date.strftime("%Y%m%d")

        # Build YouTube rank dict: video_id -> rank
        yt_sorted = sorted(
            yt_videos,
            key=lambda v: int(v["statistics"]["viewCount"]),
            reverse=True,
        )
        yt_rank = {v["id"]: rank for rank, v in enumerate(yt_sorted, start=1)}

        # Collect matched pairs: (spotify_rank, youtube_rank)
        xs = []  # Spotify ranks
        ys = []  # YouTube ranks
        names = []

        for t in sp_tracks:
            sp_id = t["id"]
            sp_rank = t["position"]
            yt_id = mapping.get(sp_id)
            if yt_id is None:
                continue
            if yt_id not in yt_rank:
                continue
            ys.append(yt_rank[yt_id])
            xs.append(sp_rank)
            names.append((t["name"], t["artists"]))

        if not xs:
            print(f"[3d] No matched tracks for date {date}.")
            continue

        corr = _spearman_correlation(xs, ys)
        print(
            f"[3d] Date {date}: matched {len(xs)} tracks. "
            f"Spearman correlation (Spotify vs YouTube rank): {corr:.3f}"
        )

        # Scatter plot
        plt.figure()
        plt.scatter(xs, ys)
        plt.xlabel("Spotify rank (1 = best)")
        plt.ylabel("YouTube rank (1 = most viewed)")
        plt.title(f"Spotify vs YouTube ranks – {date}\nSpearman ≈ {corr:.3f}")
        plt.gca().invert_xaxis()  # optional, so "better" ranks are on the left
        plt.gca().invert_yaxis()  # "better" ranks at top
        plt.tight_layout()

        out_path = os.path.join(
            PLOTS_DIR, f"s3d_rank_scatter_{date_str}.png"
        )
        plt.savefig(out_path, dpi=150)
        plt.close()

        print("   Example matched songs (Spotify rank -> YouTube rank):")
        for (sp_r, yt_r, (name, artists)) in list(
            sorted(zip(xs, ys, names), key=lambda t: t[0])
        )[:5]:
            print(f"   - {name} – {artists}: Spotify {sp_r}, YouTube {yt_r}")


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    print("Running Assignment 3 (Rich-Get-Richer) analyses...")
    print("Part 3a: plotting view-count distributions")
    plot_viewcount_distributions(num_days=5)

    # 3b and 3c are mainly theoretical / interpretative – handled in report.

    print("Part 3d: comparing Spotify and YouTube rankings")
    compare_spotify_youtube_rankings(num_days=5)


if __name__ == "__main__":
    main()
