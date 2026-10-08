"""Download configured Reddit corpora in ConvoKit's original format."""

from pathlib import Path

from convokit import download
from tqdm import tqdm

from digital_media_analysis.config_reader import get_config


def main() -> None:
    subreddits = get_config("reddit_subreddits")
    if not isinstance(subreddits, list) or not all(
        isinstance(name, str) for name in subreddits
    ):
        raise ValueError("'reddit_subreddits' must be a list of names in config.yaml.")

    output_dir = Path("./data/raw/reddit").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    for subreddit_name in tqdm(subreddits, desc="Downloading Reddit corpora"):
        corpus_path = download(
            f"subreddit-{subreddit_name}",
            data_dir=str(output_dir),
        )
        print(f"Downloaded r/{subreddit_name} to {corpus_path}")


if __name__ == "__main__":
    main()
