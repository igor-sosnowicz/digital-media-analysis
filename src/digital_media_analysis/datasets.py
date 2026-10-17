"""Load the raw Reddit and Wikipedia downloads into flat tables."""

import json
from collections.abc import Collection
from pathlib import Path
from urllib.parse import unquote

import pandas as pd

from digital_media_analysis.paths import RAW_REDDIT_DIR, RAW_WIKIPEDIA_DIR


def load_reddit_posts(data_dir: Path = RAW_REDDIT_DIR) -> pd.DataFrame:
    """Return all posts from `subreddit-*.csv` files, with empty strings for missing text."""
    files = sorted(data_dir.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No Reddit CSV files in {data_dir}; run `make pipeline`.")
    posts = pd.concat(
        [pd.read_csv(path, dtype={"id": str}) for path in files], ignore_index=True
    )
    for column in ["title", "text", "url", "created_at_utc"]:
        posts[column] = posts[column].fillna("").astype(str)
    return posts


def load_wikipedia_revisions(
    data_dir: Path = RAW_WIKIPEDIA_DIR, with_content: Collection[tuple[str, int]] = ()
) -> pd.DataFrame:
    """Return one row per revision: page, url, revision_number, introduced and comment.

    Page titles and 1-based revision numbers match `notebooks/Wikipedia_EDA.ipynb`.
    Revision content (the full article text after the edit) is dropped to keep the
    table small, except for the (page, revision_number) pairs in `with_content`:
    then a `new_content` column holds it for those rows and is empty elsewhere.
    """
    files = sorted(data_dir.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No Wikipedia JSON files in {data_dir}; run `make pipeline`.")
    with_content = set(with_content)
    records = []
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        url = payload.get("url")
        page = unquote(url.rsplit("/", 1)[-1]) if url else path.stem
        page = page.replace("_", " ")
        for revision_number, edit in enumerate(payload.get("edits", []), start=1):
            record = {
                "page": page,
                "url": url or "",
                "revision_number": revision_number,
                "introduced": edit.get("introduced") or "",
                "comment": (edit.get("comment") or "").strip(),
            }
            if with_content:
                keep = (page, revision_number) in with_content
                record["new_content"] = (edit.get("new_content") or "") if keep else ""
            records.append(record)
    return pd.DataFrame(records)
