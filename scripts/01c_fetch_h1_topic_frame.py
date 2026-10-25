"""Download the frame of H1 v2 into data/raw/reddit_h1v2/: posts about consensus topics and their top-level comments.

For every subreddit of `hypotheses_v2.h1.subreddits` and year of the period, it
downloads every post on `days_per_month` random days of each month (the whole
year when those days hold fewer than `census_below` posts), keeps the posts
whose title or body is about a consensus topic (topics_v1, codebook/topics.yaml)
and, for each of them, the first `comments_scanned_per_post` top-level
comments, of which `comments_per_post` are drawn at random. Authors are kept
(they stay outside git; samples in the repository hold a pseudonym). One file
per year for posts and one for comments; years already downloaded are skipped.
`--subreddits` and `--years` narrow a run, to check the download first.
Needs the committed preregistration v2.
"""

import argparse
import csv
import json
from datetime import UTC, datetime, timedelta

import httpx
import numpy as np
from tqdm import tqdm

from digital_media_analysis import h1_frame, reddit_archive, topics
from digital_media_analysis.config_reader import get_hypotheses_v2
from digital_media_analysis.paths import RAW_H1V2_DIR
from digital_media_analysis.prereg import require_committed

SEED = 20261025


def write(rows: list[dict], columns: list[str], path) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subreddits", nargs="+", help="Only these subreddits (of the configured ones).")
    parser.add_argument("--years", nargs="+", type=int, help="Only these years.")
    args = parser.parse_args()
    commit = require_committed()
    settings = get_hypotheses_v2()["h1"]
    subreddits = [name for name in settings["subreddits"] if not args.subreddits or name in args.subreddits]
    first, last = settings["period"]
    found_topics = topics.load_topics()
    RAW_H1V2_DIR.mkdir(parents=True, exist_ok=True)
    log_path = RAW_H1V2_DIR / "fetch_log.json"
    log = json.loads(log_path.read_text(encoding="utf-8")) if log_path.exists() else {"years": {}}
    log.update({"commit": commit, "seed": SEED, "subreddits": subreddits, "api": reddit_archive.API_URL})
    rng = np.random.default_rng(SEED)
    with httpx.Client(headers={"User-Agent": reddit_archive.USER_AGENT}, timeout=120) as client:
        for year in tqdm(range(first, last + 1), desc="H1 v2 frame"):
            days = reddit_archive.draw_days(year, int(settings["days_per_month"]), rng)
            comment_rng = np.random.default_rng([SEED, year])
            posts_path, comments_path = RAW_H1V2_DIR / f"posts-{year}.csv", RAW_H1V2_DIR / f"comments-{year}.csv"
            if (args.years and year not in args.years) or posts_path.exists():
                continue
            posts, comments, counts = [], [], {}
            whole = (datetime(year, 1, 1, tzinfo=UTC), datetime(year + 1, 1, 1, tzinfo=UTC))
            for name in subreddits:
                found = []
                for day, weight in days:
                    start = datetime(day.year, day.month, day.day, tzinfo=UTC)
                    found += [{**post, "day_weight": weight} for post in reddit_archive.fetch_window(client, name, start, start + timedelta(days=1))]
                mode = "days"
                if len(found) < int(settings["census_below"]):
                    mode, found = "census", [{**post, "day_weight": 1.0} for post in reddit_archive.fetch_window(client, name, *whole)]
                on_topic = 0
                for post in found:
                    hits = topics.matches(f"{post.get('title', '')}\n{post.get('selftext', '')}", found_topics)
                    if not hits:
                        continue
                    on_topic += 1
                    post = {**post, "topics": ";".join(code for code in found_topics if code in hits)}
                    posts.append(h1_frame.post_record(post, post["topics"]))
                    scanned = h1_frame.fetch_top_level_comments(client, post["id"], int(settings["comments_scanned_per_post"]))
                    chosen = h1_frame.choose(scanned, int(settings["comments_per_post"]), comment_rng)
                    comments += [h1_frame.comment_record(comment, post, len(scanned), len(chosen)) for comment in chosen]
                counts[name] = {"mode": mode, "posts": len(found), "on_topic": on_topic}
            write(posts, h1_frame.POST_COLUMNS, posts_path)
            write(comments, h1_frame.COMMENT_COLUMNS, comments_path)
            log["years"][str(year)] = {"fetched_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                                       "days": [day.isoformat() for day, _ in days], "subreddits": counts,
                                       "posts": len(posts), "comments": len(comments)}
            log_path.write_text(json.dumps(log, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"{year}: {len(posts)} posts on topic, {len(comments)} comments")


if __name__ == "__main__":
    main()
