import json
from datetime import UTC, datetime

import pandas as pd
import pytest

from digital_media_analysis import datasets, gold, sample_export

PERIOD = (datetime(2020, 1, 1, tzinfo=UTC), datetime(2022, 1, 1, tzinfo=UTC))
TOTALS = {"reddit": 10, "wikipedia": 12}
COMMENTS = ["", "dodano przypis", "drobne", "https://who.int/x"]


def make_posts() -> pd.DataFrame:
    return pd.DataFrame([
        {"subreddit": "lodz", "id": f"p{i:02d}", "title": f"Tytuł {i}", "text": "Zażółć\ngęślą jaźń",
         "created_utc": 1_600_000_000 + i, "created_at_utc": f"{2020 + i % 2}-03-{i % 28 + 1:02d}T12:00:00+00:00",
         "url": "", "permalink": f"/r/lodz/comments/p{i:02d}/", "score": i, "num_comments": 0, "removed_by_category": None}
        for i in range(30)
    ])


def write_wikipedia(data_dir):
    for name in ["Zmiana_klimatu", "Szczepionka"]:
        edits = [
            {"introduced": f"{2020 + i % 2}-05-{i % 28 + 1:02d}T10:00:00Z", "comment": COMMENTS[i % 4],
             "new_content": f"Artykuł {name} {i}\nŁódź"}
            for i in range(24)
        ]
        payload = {"url": f"https://pl.wikipedia.org/wiki/{name}", "edits": edits}
        (data_dir / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return data_dir


@pytest.fixture
def drawn(tmp_path):
    posts = make_posts()
    data_dir = write_wikipedia(tmp_path)
    units = gold.wikipedia_units(datasets.load_wikipedia_revisions(data_dir))
    periods = {"reddit": PERIOD, "wikipedia": PERIOD}
    manifest, design = gold.draw_sample(gold.reddit_units(posts), units, seed=3, periods=periods, totals=TOTALS)
    revisions = datasets.load_wikipedia_revisions(data_dir, with_content=sample_export.wikipedia_keys(manifest))
    return manifest, design, posts, revisions


def test_wikipedia_content_is_loaded_only_for_requested_revisions(tmp_path):
    data_dir = write_wikipedia(tmp_path)
    assert "new_content" not in datasets.load_wikipedia_revisions(data_dir)
    revisions = datasets.load_wikipedia_revisions(data_dir, with_content={("Szczepionka", 2)})
    with_text = revisions[revisions["new_content"].ne("")]
    assert with_text[["page", "revision_number"]].values.tolist() == [["Szczepionka", 2]]
    assert with_text["url"].item() == "https://pl.wikipedia.org/wiki/Szczepionka"


def test_reddit_sample_has_every_raw_column_then_the_sampling_columns(drawn):
    manifest, _, posts, _ = drawn
    sample = sample_export.reddit_sample(manifest, posts)
    assert list(sample.columns) == ["unit_id", *posts.columns, *sample_export.SAMPLING_COLUMNS]
    assert len(sample) == TOTALS["reddit"]
    assert sample.groupby("year").size().to_dict() == {2020: 5, 2021: 5}
    assert sample["text"].eq("Zażółć\ngęślą jaźń").all()
    assert sample["year"].is_monotonic_increasing


def test_wikipedia_sample_holds_the_article_text(drawn):
    manifest, _, _, revisions = drawn
    sample = sample_export.wikipedia_sample(manifest, revisions)
    assert list(sample.columns[:8]) == [
        "unit_id", "page", "url", "revision_number", "introduced", "comment", "new_content", "content_chars",
    ]
    assert len(sample) == TOTALS["wikipedia"]
    assert sample["new_content"].str.startswith("Artykuł").all()
    assert sample["content_chars"].eq(sample["new_content"].str.len()).all()
    with pytest.raises(ValueError, match="with_content"):
        sample_export.wikipedia_sample(manifest, revisions.drop(columns="new_content"))


def test_missing_unit_fails_the_export(drawn):
    manifest, _, posts, _ = drawn
    sampled = manifest.loc[manifest["platform"].eq("reddit"), "unit_id"].iloc[0]
    with pytest.raises(ValueError, match="missing"):
        sample_export.reddit_sample(manifest, posts[posts["id"].ne(sampled)])


def test_check_snapshot_detects_changed_data(drawn):
    _, design, posts, _ = drawn
    sample_export.check_snapshot(design, "reddit", gold.reddit_units(posts))
    with pytest.raises(ValueError, match="not the snapshot"):
        sample_export.check_snapshot(design, "reddit", gold.reddit_units(posts.iloc[1:]))


def test_written_files_keep_text_and_open_as_utf8_in_excel(drawn, tmp_path):
    manifest, _, posts, revisions = drawn
    samples = {
        "reddit": sample_export.reddit_sample(manifest, posts),
        "wikipedia": sample_export.wikipedia_sample(manifest, revisions),
    }
    paths = sample_export.write_samples(samples, tmp_path / "samples")
    assert paths["reddit"].read_bytes().startswith(b"\xef\xbb\xbf")
    read_back = pd.read_csv(paths["wikipedia"], encoding=sample_export.CSV_ENCODING)
    assert read_back["new_content"].tolist() == samples["wikipedia"]["new_content"].tolist()
    assert len(pd.read_csv(paths["reddit"], encoding=sample_export.CSV_ENCODING)) == TOTALS["reddit"]
