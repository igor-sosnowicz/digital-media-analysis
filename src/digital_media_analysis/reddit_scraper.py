"""Module with a Reddit scraper."""

from pathlib import Path
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from threading import local
from typing import Iterable

import praw
from prawcore.exceptions import Forbidden
from tqdm import tqdm


class NotPublicSubredditError(RuntimeError):
    """Raised when the subreddit is not public or cannot be accessed."""


def parse_utc(value: str | datetime) -> datetime:
    """Accept an ISO date/datetime string or an aware datetime; return UTC."""
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise ValueError("Dates must include a timezone, such as 2020-01-01T00:00:00Z.")
    return value.astimezone(UTC)


class RedditDiscussionScraper:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str,
        max_concurrent: int = 3,
    ):
        if not 1 <= max_concurrent <= 3:
            raise ValueError("max_concurrent must be between 1 and 3.")

        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        self.max_concurrent = max_concurrent
        self._thread_local = local()

    def _get_reddit(self) -> praw.Reddit:
        """Create one PRAW client per worker thread."""
        if not hasattr(self._thread_local, "reddit"):
            self._thread_local.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent,
            )
        return self._thread_local.reddit

    def fetch_posts(
        self,
        subreddit_name: str,
        start: str | datetime = "2016-01-01T00:00:00Z",
        end: str | datetime = "2027-01-01T00:00:00Z",
        query: str | None = None,
        max_items: int | None = 1000,
    ) -> list[dict]:
        """Fetch accessible posts in a UTC date range from a public subreddit.

        The end date is exclusive. With a query, Reddit search is used;
        without one, the subreddit’s newest-post listing is used.
        """
        start_ts = parse_utc(start).timestamp()
        end_ts = parse_utc(end).timestamp()
        if end_ts <= start_ts:
            raise ValueError("'end' must be later than 'start'.")
        if max_items is not None and max_items < 0:
            raise ValueError("max_items must be non-negative or None.")

        reddit = self._get_reddit()

        try:
            subreddit = reddit.subreddit(subreddit_name)
            subreddit_type = subreddit.subreddit_type
        except Forbidden as exc:
            raise NotPublicSubredditError(
                f"r/{subreddit_name} is private or inaccessible."
            ) from exc

        if subreddit_type != "public":
            raise NotPublicSubredditError(
                f"r/{subreddit_name} has type {subreddit_type!r}; "
                "only 'public' subreddits are allowed."
            )

        if query:
            posts = subreddit.search(
                query,
                sort="new",
                time_filter="all",
                limit=max_items,
            )
        else:
            posts = subreddit.new(limit=max_items)

        rows = []
        for post in posts:
            created = post.created_utc
            if not start_ts <= created < end_ts:
                continue

            rows.append(
                {
                    "subreddit": str(post.subreddit),
                    "id": post.id,
                    "title": post.title,
                    "text": post.selftext,
                    "created_utc": created,
                    "created_at_utc": datetime.fromtimestamp(
                        created, tz=UTC
                    ).isoformat(),
                    "url": post.url,
                    "permalink": f"https://www.reddit.com{post.permalink}",
                    "score": post.score,
                    "num_comments": post.num_comments,
                }
            )

        return rows

    def fetch_many(
        self,
        subreddit_names: Iterable[str],
        *,
        start: str | datetime = "2016-01-01T00:00:00Z",
        end: str | datetime = "2027-01-01T00:00:00Z",
        query: str | None = None,
        max_items: int | None = 1000,
    ) -> dict[str, list[dict]]:
        """Fetch several subreddit feeds concurrently, with a progress bar."""
        names = list(subreddit_names)
        results = {}

        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            futures = {
                executor.submit(
                    self.fetch_posts,
                    name,
                    start,
                    end,
                    query,
                    max_items,
                ): name
                for name in names
            }

            for future in tqdm(
                as_completed(futures),
                total=len(futures),
                desc="Fetching subreddits",
            ):
                name = futures[future]
                results[name] = future.result()

        return results

    @staticmethod
    def save_csv(rows: list[dict], filename: str) -> None:
        output_dir = Path("./data/raw/reddit")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / Path(filename).name

        fieldnames = [
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

        with output_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
