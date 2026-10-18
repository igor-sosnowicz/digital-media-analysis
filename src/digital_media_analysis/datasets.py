"""Load the raw Reddit and Wikipedia downloads into flat tables."""

import json
import warnings
from collections.abc import Collection
from pathlib import Path
from urllib.parse import unquote

import pandas as pd

from digital_media_analysis.paths import RAW_REDDIT_DIR, RAW_WIKIPEDIA_DIR


def load_reddit_posts(data_dir: Path = RAW_REDDIT_DIR, subreddits: Collection[str] | None = None) -> pd.DataFrame:
    """Return all posts from `subreddit-*.csv` files, with empty strings for missing text.

    With `subreddits` (e.g. `reddit_subreddits` from config.yaml), posts of any
    other subreddit are dropped with a warning; names match case-insensitively.
    """
    files = sorted(data_dir.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No Reddit CSV files in {data_dir}; run `make pipeline`.")
    posts = pd.concat(
        [pd.read_csv(path, dtype={"id": str}) for path in files], ignore_index=True
    )
    for column in ["title", "text", "url", "created_at_utc"]:
        posts[column] = posts[column].fillna("").astype(str)
    if subreddits is not None:
        listed = posts["subreddit"].str.casefold().isin({name.casefold() for name in subreddits})
        if extra := sorted(posts.loc[~listed, "subreddit"].unique()):
            warnings.warn(f"{data_dir}: skipped posts of subreddits not in the config: {extra}", stacklevel=2)
        posts = posts[listed].reset_index(drop=True)
    return posts


def page_title(url: str) -> str:
    """Page title as used in unit IDs: the decoded last URL segment with spaces."""
    return unquote(url.rsplit("/", 1)[-1]).replace("_", " ")


def load_wikipedia_revisions(
    data_dir: Path = RAW_WIKIPEDIA_DIR,
    with_content: Collection[tuple[str, int]] = (),
    pages: Collection[str] | None = None,
) -> pd.DataFrame:
    """Return one row per revision: page, url, revision_number, introduced and comment.

    Page titles and 1-based revision numbers match `notebooks/Wikipedia_EDA.ipynb`.
    Revision content (the full article text after the edit) is dropped to keep the
    table small, except for the (page, revision_number) pairs in `with_content`:
    then a `new_content` column holds it for those rows and is empty elsewhere.
    With `pages` (page URLs, e.g. `wikipedia_pages` from config.yaml), files of other
    pages are skipped with a warning and a listed page without a file is an error.
    """
    files = sorted(data_dir.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No Wikipedia JSON files in {data_dir}; run `make pipeline`.")
    listed = None if pages is None else {page_title(url) for url in pages}
    with_content = set(with_content)
    records, loaded, skipped = [], set(), []
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        url = payload.get("url")
        page = page_title(url) if url else path.stem.replace("_", " ")
        if listed is not None and page not in listed:
            skipped.append(path.name)
            continue
        loaded.add(page)
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
    if skipped:
        warnings.warn(f"{data_dir}: skipped files of pages not in the config: {skipped}", stacklevel=2)
    if listed is not None and (missing := sorted(listed - loaded)):
        raise FileNotFoundError(f"No file in {data_dir} for configured pages {missing}; run `make pipeline`.")
    return pd.DataFrame(records)
