from datetime import UTC, datetime

import pandas as pd
import pytest

from digital_media_analysis import gold

PERIOD = (datetime(2016, 1, 1, tzinfo=UTC), datetime(2019, 1, 1, tzinfo=UTC))
REDDIT_VISIBLE = {2016: 12, 2017: 40, 2018: 200}
# Signal sizes per year; 2016 has fewer `cue` units than the pilot and gold quotas.
WIKIPEDIA_SIZES = {
    2016: {"link": 1, "cue": 5, "other": 60},
    2017: {"link": 0, "cue": 30, "other": 80},
    2018: {"link": 3, "cue": 40, "other": 300},
}
COMMENTS = {"link": "https://who.int/a", "cue": "źródła/przypisy", "other": "drobne redakcyjne"}
TOTALS = {"reddit": 60, "wikipedia": 100}
PERIODS = {"reddit": PERIOD, "wikipedia": PERIOD}


def make_reddit_posts() -> pd.DataFrame:
    rows = [
        {"id": f"r{year}x{i:03d}", "subreddit": ["a", "b"][i % 2], "created_at_utc": f"{year}-03-{i % 28 + 1:02d}T12:00:00+00:00",
         "title": "t", "text": "x", "url": "", "removed_by_category": None}
        for year, size in REDDIT_VISIBLE.items()
        for i in range(size)
    ]
    rows += [  # outside the study period
        {"id": f"out{i}", "subreddit": "a", "created_at_utc": timestamp, "title": "t", "text": "x", "url": "", "removed_by_category": None}
        for i, timestamp in enumerate(["2015-12-31T23:59:59+00:00", "2019-01-01T00:00:00+00:00"])
    ]
    rows += [  # removed or deleted
        {"id": "gone1", "subreddit": "a", "created_at_utc": "2018-05-01T00:00:00+00:00", "title": "t", "text": "x", "url": "", "removed_by_category": "moderator"},
        {"id": "gone2", "subreddit": "a", "created_at_utc": "2018-05-01T00:00:00+00:00", "title": "t", "text": "[removed]", "url": "", "removed_by_category": None},
        {"id": "gone3", "subreddit": "b", "created_at_utc": "2018-05-01T00:00:00+00:00", "title": "[deleted]", "text": "", "url": "", "removed_by_category": None},
    ]
    return pd.DataFrame(rows)


def make_wikipedia_units() -> pd.DataFrame:
    rows = []
    for year, sizes in WIKIPEDIA_SIZES.items():
        for signal, size in sizes.items():
            rows += [{"page": f"P{i % 3}", "introduced": f"{year}-06-{i % 28 + 1:02d}T00:00:00Z", "comment": COMMENTS[signal]}
                     for i in range(size)]
    rows.append({"page": "P0", "introduced": "2019-01-01T00:00:00Z", "comment": "poza okresem"})
    revisions = pd.DataFrame(rows)
    revisions["revision_number"] = range(1, len(revisions) + 1)
    return gold.wikipedia_units(revisions)


@pytest.fixture(scope="module")
def sample() -> tuple[pd.DataFrame, dict, pd.DataFrame, pd.DataFrame]:
    reddit = gold.reddit_units(make_reddit_posts())
    wikipedia = make_wikipedia_units()
    manifest, design = gold.draw_sample(reddit, wikipedia, seed=1, periods=PERIODS, totals=TOTALS)
    return manifest, design, reddit, wikipedia


def test_allocate_takes_the_quota_capped_by_the_stratum():
    quotas = pd.Series({"big": 8, "small": 8, "census": None, "empty": 3}, dtype=float)
    sizes = pd.Series({"big": 100, "small": 5, "census": 4})
    assert gold.allocate(sizes, quotas).to_dict() == {"big": 8, "small": 5, "census": 4, "empty": 0}


def test_year_targets_take_small_years_whole_and_share_the_rest_evenly():
    # Visible Reddit posts per year in the snapshot of 16.10.2026.
    sizes = pd.Series({2016: 34, 2017: 62, 2018: 85, 2019: 79, 2020: 1290, 2021: 1814,
                       2022: 2853, 2023: 2557, 2024: 2557, 2025: 3686, 2026: 3714})
    targets = gold.year_targets(sizes, 500)
    assert targets.sum() == 500
    assert targets[2016] == 34
    # 466 units over 10 years: the six largest years get the 6 left over.
    assert targets[[2017, 2018, 2019, 2020]].eq(46).all()
    assert targets[[2021, 2022, 2023, 2024, 2025, 2026]].eq(47).all()


def test_year_targets_repeat_until_no_year_is_too_small():
    targets = gold.year_targets(pd.Series({"a": 5, "b": 9, "c": 100}), 30)
    assert targets.to_dict() == {"a": 5, "b": 9, "c": 16}
    with pytest.raises(ValueError, match="Cannot draw"):
        gold.year_targets(pd.Series({"a": 5}), 6)


def test_split_year_takes_links_caps_cue_and_fills_with_other():
    cap = 10  # a third of 30
    assert gold.split_year(30, pd.Series({"link": 2, "cue": 40, "other": 100})) == {"link": 2, "cue": cap, "other": 28 - cap}
    assert gold.split_year(30, pd.Series({"cue": 4, "other": 100})) == {"link": 0, "cue": 4, "other": 26}
    # Too few `other` units: `cue` goes over its cap to fill the year.
    assert gold.split_year(30, pd.Series({"link": 1, "cue": 40, "other": 2})) == {"link": 1, "cue": 27, "other": 2}


def test_study_years_cover_a_partial_last_year():
    assert gold.study_years(*PERIOD) == [2016, 2017, 2018]
    assert gold.study_years(datetime(2016, 1, 1, tzinfo=UTC), datetime(2026, 10, 13, tzinfo=UTC))[-1] == 2026


def test_wikipedia_signal_uses_python_word_boundaries():
    revisions = pd.DataFrame({
        "page": "Alfa",
        "revision_number": [1, 2, 3, 4],
        "introduced": "2020-01-01T00:00:00Z",
        "comment": ["https://who.int/a", "źródła/przypisy", "wg źródła", "drobne redakcyjne"],
    })
    assert gold.wikipedia_units(revisions)["signal"].tolist() == ["link", "cue", "cue", "other"]


def test_reddit_link_skips_own_thread_and_expands_crossposts():
    posts = pd.DataFrame({
        "id": ["abc", "def", "ghi"],
        "subreddit": "lodz",
        "created_at_utc": "2026-01-01",
        "title": "t",
        "text": "",
        "url": [
            "https://www.reddit.com/r/lodz/comments/abc/tytul/",
            "/r/Polska/comments/zzz/inny/",
            "https://wiadomosci.wp.pl/x",
        ],
    })
    assert gold.reddit_units(posts)["link"].tolist() == [
        "",
        "https://www.reddit.com/r/Polska/comments/zzz/inny/",
        "https://wiadomosci.wp.pl/x",
    ]


def test_reddit_units_drop_removed_and_deleted_posts():
    units = gold.reddit_units(make_reddit_posts())
    assert not units["unit_id"].str.startswith("gone").any()
    assert len(units) == sum(REDDIT_VISIBLE.values()) + 2


def test_frame_is_the_study_period(sample):
    manifest, design, _, _ = sample
    assert set(manifest["year"]) == {2016, 2017, 2018}
    assert not manifest["unit_id"].str.startswith("out").any()
    assert design["population"]["reddit"]["units"] == sum(REDDIT_VISIBLE.values())


def test_each_platform_gets_its_total(sample):
    manifest, design, _, _ = sample
    assert manifest.groupby("platform").size().to_dict() == TOTALS
    assert {platform: allocation["total"] for platform, allocation in design["allocation"].items()} == TOTALS


def test_reddit_years_are_balanced(sample):
    manifest, design, _, _ = sample
    reddit = manifest[manifest["platform"].eq("reddit")]
    per_year = pd.crosstab(reddit["year"], reddit["phase"])
    assert per_year["pilot"].tolist() == [2, 2, 2]
    # 60 posts over 3 years: 2016 has only 12, so it is drawn whole and the others get 24 each.
    assert (per_year["pilot"] + per_year["gold"]).tolist() == [12, 24, 24]
    assert design["allocation"]["reddit"]["per_year"] == {"2016": 12, "2017": 24, "2018": 24}
    assert design["allocation"]["reddit"]["whole_years"] == [2016]
    assert reddit["stratum"].eq(reddit["year"].astype(str)).all()


def test_wikipedia_years_are_balanced_and_links_are_a_census(sample):
    manifest, design, _, wikipedia = sample
    rows = manifest[manifest["platform"].eq("wikipedia")]
    assert rows.groupby("year").size().tolist() == [33, 33, 34]
    pilot = rows[rows["phase"].eq("pilot")].groupby(["year", "signal"]).size()
    assert pilot.to_dict() == {(year, signal): n for year in WIKIPEDIA_SIZES for signal, n in [("cue", 1), ("other", 2)]}
    gold_rows = rows[rows["phase"].eq("gold")].groupby(["year", "signal"]).size()
    cap = 10  # a third of the 30 or 31 gold units of each year
    assert gold_rows.to_dict() == {
        (2016, "cue"): 4, (2016, "link"): 1, (2016, "other"): 25,
        (2017, "cue"): cap, (2017, "other"): 30 - cap,
        (2018, "cue"): cap, (2018, "link"): 3, (2018, "other"): 28 - cap,
    }
    assert design["allocation"]["wikipedia"]["whole_years"] == []
    links = wikipedia[wikipedia["signal"].eq("link")]["unit_id"]
    assert set(links) <= set(rows["unit_id"])


def test_year_summary_counts_the_frame_and_every_split(sample):
    manifest, design, reddit, _ = sample
    summary = gold.year_summary(manifest, "reddit")
    assert summary["N (rama)"].to_dict() == REDDIT_VISIBLE
    assert summary[["pilot", "dev", "test"]].sum(axis=1).tolist() == [12, 24, 24]
    assert design["per_year"]["reddit"]["2017"] == {"N (rama)": 40, "pilot": 2, "dev": 7, "test": 15}


def test_sample_is_deterministic(sample):
    manifest, _, reddit, wikipedia = sample
    again, _ = gold.draw_sample(reddit, wikipedia, seed=1, periods=PERIODS, totals=TOTALS)
    pd.testing.assert_frame_equal(manifest, again)


def test_pilot_is_disjoint_from_gold(sample):
    manifest, _, _, _ = sample
    assert not manifest["unit_id"].duplicated().any()
    assert set(manifest["split"]) == {"pilot", "dev", "test"}
    assert (manifest["phase"].eq("pilot") == manifest["split"].eq("pilot")).all()


def test_test_weights_reconstruct_every_frame_stratum(sample):
    manifest, _, _, _ = sample
    gold_rows = manifest[manifest["phase"].eq("gold")]
    test = gold_rows[gold_rows["split"].eq("test")]
    # Every stratum of the frame has test units, and their weights sum to its size.
    assert set(test["stratum"]) == set(gold_rows["stratum"])
    totals = test.groupby("stratum")["weight"].sum()
    sizes = gold_rows.groupby("stratum")["N_h"].first()
    pd.testing.assert_series_equal(totals, sizes.astype(float), check_names=False)


def test_order_is_a_permutation_within_each_split(sample):
    manifest, _, _, _ = sample
    for _, rows in manifest.groupby(["platform", "split"]):
        assert sorted(rows["order"]) == list(range(1, len(rows) + 1))


def test_save_refuses_to_overwrite(tmp_path, sample):
    manifest, design, _, _ = sample
    paths = {"manifest_path": tmp_path / "m.csv", "design_path": tmp_path / "d.json"}
    gold.save_sample(manifest, design, **paths)
    with pytest.raises(FileExistsError):
        gold.save_sample(manifest, design, **paths)
    gold.save_sample(manifest, design, force=True, **paths)
    pd.testing.assert_frame_equal(gold.load_manifest(paths["manifest_path"]), manifest, check_dtype=False)


def test_attach_units_detects_a_changed_snapshot(sample):
    manifest, _, reddit, _ = sample
    rows = manifest[manifest["platform"].eq("reddit")]
    assert gold.attach_units(rows, reddit)["text"].eq("x").all()
    with pytest.raises(ValueError, match="missing"):
        gold.attach_units(rows, reddit[reddit["unit_id"].ne(rows["unit_id"].iloc[0])])
    shifted = reddit.assign(introduced="2030-01-01")
    with pytest.raises(ValueError, match="timestamp"):
        gold.attach_units(rows, shifted)


def test_each_platform_has_its_own_study_period():
    reddit = gold.reddit_units(make_reddit_posts())
    periods = {"reddit": PERIOD, "wikipedia": (datetime(2017, 1, 1, tzinfo=UTC), datetime(2019, 1, 1, tzinfo=UTC))}
    manifest, design = gold.draw_sample(reddit, make_wikipedia_units(), seed=1, periods=periods, totals=TOTALS)
    years = manifest.groupby("platform")["year"].unique().map(sorted).to_dict()
    assert years == {"reddit": [2016, 2017, 2018], "wikipedia": [2017, 2018]}
    assert design["study_period"]["wikipedia"]["years"] == [2017, 2018]


def test_day_weights_scale_reddit_weights_up_to_the_month():
    posts = make_reddit_posts().assign(day_weight=31.0)
    manifest, design = gold.draw_sample(gold.reddit_units(posts), make_wikipedia_units(), seed=1, periods=PERIODS, totals=TOTALS)
    reddit = manifest[manifest["platform"].eq("reddit")]
    pd.testing.assert_series_equal(reddit["weight"], reddit["N_h"] / reddit["n_h"] * 31, check_names=False)
    assert design["reddit"]["estimated_posts_per_year"] == {str(year): 31 * n for year, n in REDDIT_VISIBLE.items()}
