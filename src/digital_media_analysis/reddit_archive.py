"""Download every post of a subreddit in a time window from the Arctic Shift Reddit archive."""

import calendar
import csv
import time
from datetime import date, datetime, timezone
from pathlib import Path

import httpx
import numpy as np

API_URL = "https://arctic-shift.photon-reddit.com/api/posts/search"
USER_AGENT = "digital-media-analysis/1.0"
PAGE_SIZE = 100
# The archive answers 422 "Timeout. Maybe slow down" when it is busy.
RETRY_STATUSES = {422, 429, 500, 502, 503, 504}
MAX_ATTEMPTS = 6
PAUSE_SECONDS = 1.0
# The schema of `01_fetch_reddit_data.py` plus the removal marker and the day
# weight of the frame download, so `datasets.load_reddit_posts` reads both.
COLUMNS = [
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
    "removed_by_category",
    "day_weight",
]


def fetch_window(client: httpx.Client, subreddit: str, start: datetime, end: datetime) -> list[dict]:
    """Return every archived post with `start <= created_utc < end`, oldest first.

    The API's `after` and `before` are exclusive and a page holds at most
    `PAGE_SIZE` posts sorted by creation time. Each next page starts one second
    before the last post seen and repeated IDs are dropped, so posts sharing a
    timestamp across a page boundary are kept.
    """
    first, stop = int(start.timestamp()), int(end.timestamp())
    posts: dict[str, dict] = {}
    cursor = first - 1
    while True:
        page = _get(client, API_URL, {
            "subreddit": subreddit,
            "after": cursor,
            "before": stop,
            "sort": "asc",
            "limit": PAGE_SIZE,
        })
        new = [post for post in page if post["id"] not in posts]
        posts.update((post["id"], post) for post in new)
        if len(page) < PAGE_SIZE:
            return list(posts.values())
        if not new:
            raise RuntimeError(
                f"r/{subreddit}: more than {PAGE_SIZE} posts share created_utc={page[-1]['created_utc']}; "
                "the archive cannot be paged past them."
            )
        cursor = int(page[-1]["created_utc"]) - 1
        time.sleep(PAUSE_SECONDS)


def draw_days(year: int, per_month: int, rng: np.random.Generator) -> list[tuple[date, float]]:
    """`per_month` distinct random days of every month of `year`, each with its weight.

    The weight is the inverse probability that a day of that month was drawn
    (days in the month / `per_month`), so it scales posts on drawn days up to the month.
    """
    days = []
    for month in range(1, 13):
        length = calendar.monthrange(year, month)[1]
        for day in sorted(rng.choice(length, size=per_month, replace=False) + 1):
            days.append((date(year, month, int(day)), length / per_month))
    return days


def _get(client: httpx.Client, url: str, params: dict) -> list[dict]:
    """GET one archive endpoint and return its `data` list, retrying busy or failed requests."""
    for attempt in range(MAX_ATTEMPTS):
        last_attempt = attempt == MAX_ATTEMPTS - 1
        try:
            response = client.get(url, params=params)
        except httpx.TransportError:
            if last_attempt:
                raise
        else:
            if response.status_code not in RETRY_STATUSES or last_attempt:
                response.raise_for_status()
                data = response.json().get("data")
                if not isinstance(data, list):
                    raise ValueError(f"Unexpected archive response for {params}: missing data list.")
                return data
        time.sleep(2**attempt)
    raise AssertionError("unreachable")


def post_row(post: dict) -> dict:
    """Flatten one archive record into the CSV schema."""
    created_utc = post.get("created_utc")
    created_at = (
        datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat()
        if isinstance(created_utc, (int, float))
        else ""
    )
    return {
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
        "removed_by_category": post.get("removed_by_category") or "",
        # Set by the frame download; a whole-period download stands for itself.
        "day_weight": post.get("day_weight", 1.0),
    }


def write_posts(posts: list[dict], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(post_row(post) for post in posts)
