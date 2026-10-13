"""Download configured Reddit posts as CSV files."""

import csv
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from tqdm import tqdm

from digital_media_analysis.config_reader import get_config


API_URL = "https://arctic-shift.photon-reddit.com/api/posts/search"
DEFAULT_LIMIT = 50


def fetch_subreddit(subreddit: str, limit: int = DEFAULT_LIMIT) -> list[dict]:
    """Fetch recent posts for one subreddit from the Reddit archive API."""
    last_response: httpx.Response | None = None
    for requested_limit in (limit, min(limit, 25), 10):
        response = httpx.get(
            API_URL,
            params={"subreddit": subreddit, "limit": requested_limit},
            headers={"User-Agent": "digital-media-analysis/1.0"},
            timeout=60,
        )
        if response.status_code != 422:
            response.raise_for_status()
            break
        last_response = response
        time.sleep(2)
    else:
        assert last_response is not None
        last_response.raise_for_status()
    payload = response.json()
    posts = payload.get("data")
    if not isinstance(posts, list):
        raise ValueError(f"Unexpected response for r/{subreddit}: missing data list.")
    return posts


def write_posts(posts: list[dict], output_path: Path) -> None:
    """Write archive records in the stable schema consumed by the EDA notebook."""
    columns = [
        "subreddit",
        "id",
        "title",
        "text",
        "created_utc",
        "created_at_utc",
        "url",
        "permalink",
        "score",
        "num_comments",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for post in posts:
            created_utc = post.get("created_utc")
            created_at = (
                datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat()
                if isinstance(created_utc, (int, float))
                else ""
            )
            writer.writerow(
                {
                    "subreddit": post.get("subreddit", ""),
                    "id": post.get("id", ""),
                    "title": post.get("title", ""),
                    "text": post.get("selftext", ""),
                    "created_utc": created_utc,
                    "created_at_utc": created_at,
                    "url": post.get("url", ""),
                    "permalink": post.get("permalink", ""),
                    "score": post.get("score", 0),
                    "num_comments": post.get("num_comments", 0),
                }
            )


def main() -> None:
    subreddits = get_config("reddit_subreddits")
    if not isinstance(subreddits, list) or not all(
        isinstance(name, str) for name in subreddits
    ):
        raise ValueError("'reddit_subreddits' must be a list of names in config.yaml.")

    output_dir = Path("./data/raw/reddit").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    for subreddit_name in tqdm(subreddits, desc="Downloading Reddit corpora"):
        posts = fetch_subreddit(subreddit_name)
        output_path = output_dir / f"subreddit-{subreddit_name}.csv"
        write_posts(posts, output_path)
        print(f"Downloaded {len(posts)} posts from r/{subreddit_name} to {output_path}")


if __name__ == "__main__":
    main()
