"""Data enters the frames only from the subreddits and pages config.yaml lists."""

import json

import pandas as pd
import pytest

from digital_media_analysis import config_reader, datasets, gold

POST = {"title": "t", "text": "x", "url": "", "removed_by_category": None}


def write_posts(path, rows: list[dict]) -> None:
    pd.DataFrame([{**POST, **row} for row in rows]).to_csv(path, index=False)


def write_page(path, url: str, comments: list[str]) -> None:
    edits = [{"introduced": "2021-01-01T00:00:00Z", "comment": comment, "new_content": "tekst"} for comment in comments]
    path.write_text(json.dumps({"url": url, "edits": edits}), encoding="utf-8")


def test_reddit_subreddits_accept_names_and_year_ranges(monkeypatch):
    monkeypatch.setattr(config_reader, "get_config", lambda key: ["science", {"reddit.com": [2005, 2005]}])
    assert config_reader.get_reddit_subreddits() == {"science": None, "reddit.com": (2005, 2005)}


@pytest.mark.parametrize(
    ("entries", "message"),
    [
        ([{"science": [2010, 2006]}], "first year"),
        ([{"science": [2006, 2010], "skeptic": [2008, 2010]}], "Invalid entry"),
        ("science", "must be a list"),
    ],
)
def test_invalid_reddit_subreddits_are_rejected(monkeypatch, entries, message):
    monkeypatch.setattr(config_reader, "get_config", lambda key: entries)
    with pytest.raises(ValueError, match=message):
        config_reader.get_reddit_subreddits()


def test_frame_subreddits_respect_year_ranges():
    subreddits = {"science": None, "reddit.com": (2005, 2005)}
    assert gold.frame_subreddits(subreddits, 2005) == ["science", "reddit.com"]
    assert gold.frame_subreddits(subreddits, 2006) == ["science"]


def test_reddit_posts_keep_only_listed_subreddits(tmp_path):
    write_posts(tmp_path / "posts-2010.csv", [
        {"id": "a", "subreddit": "Science", "created_at_utc": "2010-05-01T00:00:00+00:00"},
        {"id": "b", "subreddit": "AskReddit", "created_at_utc": "2010-05-01T00:00:00+00:00"},
    ])
    with pytest.warns(UserWarning, match="AskReddit"):
        posts = datasets.load_reddit_posts(tmp_path, subreddits=["science"])
    assert posts["id"].tolist() == ["a"]


def test_reddit_frame_keeps_each_subreddit_in_its_configured_years(tmp_path, monkeypatch):
    write_posts(tmp_path / "posts.csv", [
        {"id": "r2005", "subreddit": "reddit.com", "created_at_utc": "2005-07-01T00:00:00+00:00"},
        {"id": "r2007", "subreddit": "reddit.com", "created_at_utc": "2007-07-01T00:00:00+00:00"},
        {"id": "s2007", "subreddit": "science", "created_at_utc": "2007-07-01T00:00:00+00:00"},
        {"id": "x2007", "subreddit": "AskReddit", "created_at_utc": "2007-07-01T00:00:00+00:00"},
    ])
    monkeypatch.setattr(gold, "RAW_REDDIT_FRAME_DIR", tmp_path)
    monkeypatch.setattr(gold, "get_reddit_subreddits", lambda: {"science": None, "reddit.com": (2005, 2005)})
    with pytest.warns(UserWarning, match="AskReddit"):
        frame = gold.load_reddit_frame()
    assert frame["id"].tolist() == ["r2005", "s2007"]


def test_wikipedia_revisions_keep_only_listed_pages(tmp_path):
    write_page(tmp_path / "Lekarz.json", "https://pl.wikipedia.org/wiki/Lekarz", ["a", "b"])
    write_page(tmp_path / "Inna.json", "https://pl.wikipedia.org/wiki/Inna_strona", ["c"])
    write_page(tmp_path / "Zespol.json", "https://pl.wikipedia.org/wiki/Zesp%C3%B3%C5%82_X", ["d"])
    # Encoded and decoded URLs name the same page.
    pages = ["https://pl.wikipedia.org/wiki/Lekarz", "https://pl.wikipedia.org/wiki/Zespół_X"]
    with pytest.warns(UserWarning, match="Inna.json"):
        revisions = datasets.load_wikipedia_revisions(tmp_path, pages=pages)
    assert revisions["page"].tolist() == ["Lekarz", "Lekarz", "Zespół X"]


def test_listed_page_without_a_file_is_an_error(tmp_path):
    write_page(tmp_path / "Lekarz.json", "https://pl.wikipedia.org/wiki/Lekarz", ["a"])
    pages = ["https://pl.wikipedia.org/wiki/Lekarz", "https://pl.wikipedia.org/wiki/Medycyna"]
    with pytest.raises(FileNotFoundError, match="Medycyna"):
        datasets.load_wikipedia_revisions(tmp_path, pages=pages)


def test_config_lists_the_sources_of_the_current_data():
    subreddits = config_reader.get_reddit_subreddits()
    assert {"PolskaPolityka", "science", "reddit.com"} <= set(subreddits)
    assert all(page.startswith("https://pl.wikipedia.org/wiki/") for page in config_reader.get_wikipedia_pages())
