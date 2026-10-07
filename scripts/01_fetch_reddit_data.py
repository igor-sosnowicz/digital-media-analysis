"""Script for scraping configured Reddit subreddits."""

from digital_media_analysis.config_reader import get_config
from digital_media_analysis.reddit_scraper import RedditDiscussionScraper


def main() -> None:
    subreddits = get_config("reddit_subreddits")
    if not isinstance(subreddits, list) or not all(
        isinstance(name, str) for name in subreddits
    ):
        raise ValueError("'reddit_subreddits' must be a list of names in config.yaml.")

    scraper = RedditDiscussionScraper(
        client_id=get_config("client_id"),
        client_secret=get_config("client_secret"),
        user_agent=get_config("user_agent"),
        max_concurrent=get_config("max_concurrent"),
    )

    feeds = scraper.fetch_many(
        subreddits,
        start="2016-01-01T00:00:00Z",
        end="2027-01-01T00:00:00Z",
        max_items=1000,
    )

    for subreddit_name, posts in feeds.items():
        scraper.save_csv(posts, f"{subreddit_name}_posts.csv")
        print(f"Saved {len(posts)} posts from r/{subreddit_name}.")


if __name__ == "__main__":
    main()
