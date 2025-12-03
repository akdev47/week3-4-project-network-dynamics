"""
Assignment 5(b) – Analyze your own YouTube hip hop dataset
----------------------------------------------------------

This script:
- Loads the JSON dataset produced by assignment5_collect_dataset.py
- Extracts view counts
- Produces two plots for Section 5(b):

  1) Popularity distribution (linear scale)
  2) Rank vs popularity (log-log style, like Figure 18.4)
"""

import os
import json

import numpy as np
import matplotlib.pyplot as plt

DATA_PATH = os.path.join("data", "my_hiphop_youtube_dataset.json")


def load_view_counts(path=DATA_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Dataset not found at {path}. Run assignment5_collect_dataset.py first."
        )

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data["items"]
    view_counts = [v["viewCount"] for v in items if v.get("viewCount") is not None]

    return np.array(view_counts), data


def plot_linear_distribution(view_counts, output_path):
    """
    Plot the popularity distribution on a linear scale.

    We sort videos by view count (descending) and plot view count vs rank.
    """
    sorted_views = np.sort(view_counts)[::-1]
    ranks = np.arange(1, len(sorted_views) + 1)

    plt.figure(figsize=(8, 5))
    plt.plot(ranks, sorted_views, marker=".", linewidth=1)
    plt.xlabel("Rank (1 = most viewed)")
    plt.ylabel("View count")
    plt.title("Popularity distribution of hip hop videos (linear scale)")
    plt.grid(True, linestyle="--", linewidth=0.5)
    plt.tight_layout()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    print(f"Saved linear distribution plot to {output_path}")
    plt.close()


def plot_rank_popularity_loglog(view_counts, output_path):
    """
    Plot rank vs popularity on a log-log scale, like Figure 18.4.
    """
    sorted_views = np.sort(view_counts)[::-1]
    ranks = np.arange(1, len(sorted_views) + 1)

    plt.figure(figsize=(8, 5))
    plt.loglog(ranks, sorted_views, marker=".", linestyle="none")
    plt.xlabel("Rank (log scale)")
    plt.ylabel("View count (log scale)")
    plt.title("Rank–popularity plot of hip hop videos (log–log)")
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.tight_layout()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    print(f"Saved rank–popularity log-log plot to {output_path}")
    plt.close()


def main():
    view_counts, meta = load_view_counts()
    print(f"Loaded dataset with {len(view_counts)} videos.")
    print(f"Query used: {meta.get('query')}")

    plot_linear_distribution(
        view_counts,
        output_path=os.path.join("figures", "a5_linear_popularity.png"),
    )
    plot_rank_popularity_loglog(
        view_counts,
        output_path=os.path.join("figures", "a5_rank_popularity_loglog.png"),
    )


if __name__ == "__main__":
    main()
