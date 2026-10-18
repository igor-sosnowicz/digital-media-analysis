"""Download the Reddit sampling frame into `data/raw/reddit_frame/`, one CSV per year.

The frame covers only the subreddits in `reddit_subreddits` (config.yaml), in the
years of the Reddit study period (`study_periods.reddit`) in which each of them
counts. For each subreddit and year it holds every post on `days_per_month`
random days of each month (`reddit_frame`); `day_weight` (days in the month /
days drawn) scales those posts up to their month. A subreddit with fewer than
`census_below` posts on the drawn days of a year is downloaded whole for that
year instead, with `day_weight` 1, so small subreddits are not lost to the draw.

Days are drawn with a fixed seed and are the same for every subreddit of a year,
so a rerun draws the same days. Years that already have a CSV are skipped, so an
interrupted run can be resumed; `fetch_log.json` records the days and, for every
subreddit and year, the mode and the number of posts.
`01_fetch_reddit_data.py` (the newest posts, for the EDA notebook) is separate.
"""

import argparse
import json
from datetime import UTC, datetime, timedelta

import httpx
import numpy as np
from tqdm import tqdm

from digital_media_analysis import reddit_archive
from digital_media_analysis.config_reader import get_config, get_reddit_subreddits, get_study_period
from digital_media_analysis.gold import frame_subreddits, study_years
from digital_media_analysis.paths import RAW_REDDIT_FRAME_DIR

SEED = 20261017
LOG_PATH = RAW_REDDIT_FRAME_DIR / "fetch_log.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Download again years that already have a CSV. Changes the frame of an existing sample.",
    )
    args = parser.parse_args()

    start, end = get_study_period("reddit")
    settings = get_config("reddit_frame")
    per_month = int(settings["days_per_month"])
    census_below = int(settings["census_below"])
    subreddits = get_reddit_subreddits()

    RAW_REDDIT_FRAME_DIR.mkdir(parents=True, exist_ok=True)
    log = json.loads(LOG_PATH.read_text(encoding="utf-8")) if LOG_PATH.exists() else {}
    log.update({
        "api": reddit_archive.API_URL,
        "study_start": start.isoformat(),
        "study_end": end.isoformat(),
        "seed": SEED,
        "days_per_month": per_month,
        "census_below": census_below,
        "subreddits": {name: list(years) if years else None for name, years in subreddits.items()},
    })
    log.setdefault("years", {})

    rng = np.random.default_rng(SEED)
    headers = {"User-Agent": reddit_archive.USER_AGENT}
    with httpx.Client(headers=headers, timeout=120) as client:
        for year in tqdm(study_years(start, end), desc="Downloading Reddit frame"):
            # Draw before skipping, so every year gets the same days on every run.
            days = reddit_archive.draw_days(year, per_month, rng)
            output_path = RAW_REDDIT_FRAME_DIR / f"posts-{year}.csv"
            if output_path.exists() and not args.force:
                print(f"{year}: {output_path.name} exists, skipped (use --force to download again)")
                continue
            whole_year = (max(datetime(year, 1, 1, tzinfo=UTC), start), min(datetime(year + 1, 1, 1, tzinfo=UTC), end))

            posts, per_subreddit = [], {}
            for name in frame_subreddits(subreddits, year):
                found = []
                for day, weight in days:
                    day_start = datetime(day.year, day.month, day.day, tzinfo=UTC)
                    window = (max(day_start, start), min(day_start + timedelta(days=1), end))
                    if window[0] < window[1]:
                        found += [
                            {**post, "day_weight": weight}
                            for post in reddit_archive.fetch_window(client, name, *window)
                        ]
                mode = "days"
                if len(found) < census_below:
                    mode = "census"
                    found = [{**post, "day_weight": 1.0} for post in reddit_archive.fetch_window(client, name, *whole_year)]
                posts += found
                per_subreddit[name] = {"mode": mode, "posts": len(found)}

            reddit_archive.write_posts(posts, output_path)
            log["years"][str(year)] = {
                "fetched_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                "days": [day.isoformat() for day, _ in days],
                "posts": len(posts),
                "subreddits": per_subreddit,
            }
            LOG_PATH.write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            summary = ", ".join(f"r/{name} {count['posts']} ({count['mode']})" for name, count in per_subreddit.items() if count["posts"])
            print(f"{year}: {len(posts)} posts: {summary or 'none'}")


if __name__ == "__main__":
    main()
