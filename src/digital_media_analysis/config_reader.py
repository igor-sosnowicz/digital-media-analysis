"""Read values from the project's config.yaml file."""

from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

CONFIG_PATH = (Path(__file__).parent.parent).with_name("config.yaml").resolve()


@lru_cache(maxsize=1)
def _load_config() -> dict[str, Any]:
    with CONFIG_PATH.open(encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}

    if not isinstance(config, dict):
        raise TypeError(f"{CONFIG_PATH} must contain a YAML mapping.")

    return config


def get_config(key: str) -> Any:
    """Return a top-level config value by key."""
    config = _load_config()
    try:
        return config[key]
    except KeyError as exc:
        raise KeyError(f"Config key {key!r} not found in {CONFIG_PATH}.") from exc


def get_reddit_subreddits() -> dict[str, tuple[int, int] | None]:
    """Return `reddit_subreddits` as {name: (first, last) frame years, or None for every year}.

    Entries are plain names or one-key mappings `name: [first, last]`.
    """
    entries = get_config("reddit_subreddits")
    if not isinstance(entries, list):
        raise ValueError(f"'reddit_subreddits' must be a list in {CONFIG_PATH}.")
    subreddits: dict[str, tuple[int, int] | None] = {}
    for entry in entries:
        if isinstance(entry, str):
            subreddits[entry] = None
        elif isinstance(entry, dict) and len(entry) == 1:
            ((name, years),) = entry.items()
            first, last = (int(year) for year in years)
            if first > last:
                raise ValueError(f"r/{name}: the first year must not be after the last in {CONFIG_PATH}.")
            subreddits[str(name)] = (first, last)
        else:
            raise ValueError(f"Invalid entry {entry!r} under reddit_subreddits in {CONFIG_PATH}; use a name or `name: [first, last]`.")
    return subreddits


def get_wikipedia_pages() -> list[str]:
    """Return the page URLs listed under `wikipedia_pages`."""
    pages = get_config("wikipedia_pages")
    if not isinstance(pages, list) or not all(isinstance(page, str) for page in pages):
        raise ValueError(f"'wikipedia_pages' must be a list of URLs in {CONFIG_PATH}.")
    return pages


def get_hypotheses() -> dict[str, Any]:
    """The `hypotheses` section, checked: H1 subreddits must be listed in `reddit_subreddits`."""
    settings = get_config("hypotheses")
    known = {name.casefold() for name in get_reddit_subreddits()}
    if unknown := sorted(name for name in settings["h1"]["subreddits"] if name.casefold() not in known):
        raise ValueError(f"hypotheses.h1.subreddits {unknown} are not in reddit_subreddits in {CONFIG_PATH}.")
    for key in ("h1", "h2"):
        first, last = settings[key]["period"]
        if first > last:
            raise ValueError(f"hypotheses.{key}.period must start before it ends in {CONFIG_PATH}.")
    return settings


def get_study_period(platform: str) -> tuple[datetime, datetime]:
    """Return a platform's study period from `study_periods` as timezone-aware UTC datetimes (end exclusive)."""
    periods = get_config("study_periods")
    if platform not in periods:
        raise KeyError(f"No study period for {platform!r} under study_periods in {CONFIG_PATH}.")
    start, end = (
        datetime.fromisoformat(str(periods[platform][key])).astimezone(timezone.utc) for key in ("start", "end")
    )
    if start >= end:
        raise ValueError(f"The {platform} study period must start before it ends in {CONFIG_PATH}.")
    return start, end
