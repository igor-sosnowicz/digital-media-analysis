"""Download the Reddit sampling frame into `data/raw/reddit_frame/`, one CSV per year.

For every year of the Reddit study period (`study_periods.reddit` in config.yaml)
the frame is every post of the subreddits listed for that year under
`reddit_frame`, on `days_per_month` random days of each month. `day_weight`
(days in the month / days drawn) scales those posts up to their month. When the
drawn days hold fewer than `census_below` posts, the whole year is downloaded
instead and every post has `day_weight` 1.

Days are drawn with a fixed seed, so a rerun draws the same days. Years that
already have a CSV are skipped, so an interrupted run can be resumed;
`fetch_log.json` records the days, the mode and the counts of every year.
`01_fetch_reddit_data.py` (the newest posts, for the EDA notebook) is separate.
"""

import argparse
import json
from collections import Counter
from datetime import UTC, datetime, timedelta

import httpx
import numpy as np
from tqdm import tqdm

from digital_media_analysis import reddit_archive
from digital_media_analysis.config_reader import get_config, get_study_period
from digital_media_analysis.gold import study_years
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
    subreddits = {name: (int(first), int(last)) for name, (first, last) in settings["subreddits"].items()}

    RAW_REDDIT_FRAME_DIR.mkdir(parents=True, exist_ok=True)
    log = json.loads(LOG_PATH.read_text(encoding="utf-8")) if LOG_PATH.exists() else {}
    log.update({
        "api": reddit_archive.API_URL,
        "study_start": start.isoformat(),
        "study_end": end.isoformat(),
        "seed": SEED,
        "days_per_month": per_month,
        "census_below": census_below,
        "subreddits": {name: list(years) for name, years in subreddits.items()},
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
            active = [name for name, (first, last) in subreddits.items() if first <= year <= last]

            posts = []
            for name in active:
                for day, weight in days:
                    day_start = datetime(day.year, day.month, day.day, tzinfo=UTC)
                    window = (max(day_start, start), min(day_start + timedelta(days=1), end))
                    if window[0] < window[1]:
                        posts += [
                            {**post, "day_weight": weight}
                            for post in reddit_archive.fetch_window(client, name, *window)
                        ]
            mode = "days"
            if len(posts) < census_below:
                mode = "census"
                window = (max(datetime(year, 1, 1, tzinfo=UTC), start), min(datetime(year + 1, 1, 1, tzinfo=UTC), end))
                posts = [
                    {**post, "day_weight": 1.0}
                    for name in active
                    for post in reddit_archive.fetch_window(client, name, *window)
                ]

            reddit_archive.write_posts(posts, output_path)
            per_subreddit = Counter(post["subreddit"] for post in posts)
            log["years"][str(year)] = {
                "fetched_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                "mode": mode,
                "days": [day.isoformat() for day, _ in days] if mode == "days" else [],
                "posts": len(posts),
                "per_subreddit": {name: per_subreddit[name] for name in active},
            }
            LOG_PATH.write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"{year}: {len(posts)} posts ({mode}) from {', '.join(f'r/{name}' for name in active) or 'no subreddit'}")


if __name__ == "__main__":
    main()
