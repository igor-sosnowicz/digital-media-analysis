import numpy as np
import pandas as pd
import pytest

from digital_media_analysis import config_reader, hypotheses


def frame_posts() -> pd.DataFrame:
    rows = []
    for subreddit, year, size in [("science", 2010, 10), ("science", 2011, 3), ("conspiracy", 2010, 6), ("lodz", 2010, 4)]:
        rows += [{"unit_id": f"{subreddit}{year}x{i}", "group": subreddit, "year": year,
                  "introduced": f"{year}-03-{i % 28 + 1:02d}T10:00:00+00:00", "day_weight": 2.0} for i in range(size)]
    return pd.DataFrame(rows)


def test_h1_analysis_sample_caps_cells_and_weights_back_to_the_frame():
    sample = hypotheses.h1_analysis_sample(frame_posts(), ["science", "conspiracy"], [2005, 2018], per_cell=4)
    counts = sample.groupby(["group", "year"]).size().to_dict()
    assert counts == {("conspiracy", 2010): 4, ("science", 2010): 4, ("science", 2011): 3}
    # Weights add up to the frame posts scaled by their day weight.
    totals = sample.groupby(["group", "year"])["weight"].sum().to_dict()
    assert totals[("science", 2010)] == pytest.approx(10 * 2.0) and totals[("science", 2011)] == pytest.approx(3 * 2.0)
    again = hypotheses.h1_analysis_sample(frame_posts(), ["science", "conspiracy"], [2005, 2018], per_cell=4)
    pd.testing.assert_frame_equal(sample, again)


def test_outcomes():
    labels = pd.DataFrame({"unit_id": ["a", "b", "c"], "cites_source": [1, 1, 0],
                           "source_types": ["scientific;media", "social_blog", "none"]})
    h1b = hypotheses.h1b_outcomes(labels, ["scientific", "institutional"], ["social_blog", "unknown", "personal"])
    assert h1b[["unit_id", "consensus", "alternative"]].values.tolist() == [["a", 1, 0], ["b", 0, 1]]
    stances = pd.DataFrame({"unit_id": ["a", "b", "c"], "consensus_stance": ["challenges", "not_applicable", "supports"]})
    h1a = hypotheses.h1a_outcomes(stances)
    assert h1a[["unit_id", "challenges", "supports"]].values.tolist() == [["a", 1, 0], ["c", 0, 1]]
    links = pd.DataFrame({"page": "P", "revision_number": [1, 2, 3], "year": pd.array([2019, 2020, 2021], dtype="Int64"),
                          "category": ["media", "social_blog", "unclassified"]})
    h2 = hypotheses.h2_outcomes(links, [2020, 2026], ["social_blog"])
    assert h2[["revision", "alternative"]].values.tolist() == [["P#2", 1], ["P#3", 0]]


def test_rogan_gladen_and_error_rates():
    assert hypotheses.rogan_gladen(0.3, 0.8, 0.9) == pytest.approx((0.3 + 0.9 - 1) / 0.7)
    assert hypotheses.rogan_gladen(0.01, 0.8, 0.9) == 0.0
    assert np.isnan(hypotheses.rogan_gladen(0.3, 0.5, 0.5))
    rates = hypotheses.error_rates(pd.Series([1, 1, 0, 0, 0]), pd.Series([1, 0, 0, 0, 1]))
    assert (rates["sensitivity"], rates["specificity"], rates["positives"]) == (0.5, pytest.approx(2 / 3), 2)


def synthetic(slope: float, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for group, offset in [("science", -1.0), ("conspiracy", 0.5)]:
        for year in range(2005, 2019):
            probability = 1 / (1 + np.exp(-(offset + slope * (year - 2005))))
            for day in range(20):
                for _ in range(5):
                    rows.append({"group": group, "year": year, "day": f"{year}-{day}", "weight": rng.uniform(0.5, 2),
                                 "outcome": int(rng.random() < probability)})
    return pd.DataFrame(rows)


def test_trend_detects_the_direction_one_sided():
    rising = synthetic(0.15)
    up = hypotheses.trend(rising, "outcome", "group", "day", "increase", 2005)
    assert up["beta"] > 0 and up["p_one_sided"] < 0.01 and up["odds_ratio_per_year"] > 1
    down = hypotheses.trend(rising, "outcome", "group", "day", "decrease", 2005)
    assert down["p_one_sided"] > 0.99
    flat = hypotheses.trend(rising.assign(outcome=0), "outcome", "group", "day", "increase", 2005)
    assert flat["note"] == "brak zmienności wyniku"


def test_yearly_shares_have_intervals_around_the_share():
    data = synthetic(0.1).query("year <= 2007").reset_index(drop=True)
    shares = hypotheses.yearly_shares(data, "outcome", strata=["group", "year"], samples=100)
    assert shares["year"].tolist() == [2005, 2006, 2007]
    assert ((shares["low"] <= shares["share"]) & (shares["share"] <= shares["high"])).all()
    by_group = hypotheses.yearly_shares(data, "outcome", by=["group"], samples=20)
    assert len(by_group) == 6


def test_hypotheses_config_checks_subreddits(monkeypatch):
    real = config_reader.get_config

    def fake(key):
        value = real(key)
        if key == "hypotheses":
            value = {**value, "h1": {**value["h1"], "subreddits": ["science", "askscience"]}}
        return value

    monkeypatch.setattr(config_reader, "get_config", fake)
    with pytest.raises(ValueError, match="askscience"):
        config_reader.get_hypotheses()


def test_clustered_errors_match_statsmodels_without_weights():
    import statsmodels.api as sm

    data = synthetic(0.1, seed=3).assign(weight=1.0)
    ours = hypotheses.trend(data, "outcome", "group", "day", "increase", 2005)
    design = pd.DataFrame({"const": 1.0, "year": data["year"] - 2005.0,
                           "fe": (data["group"] == "science").astype(float)})
    reference = sm.GLM(data["outcome"], design, family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(data["day"])[0], "use_correction": False}
    )
    clusters = data["day"].nunique()
    # statsmodels without its correction; ours adds only G / (G - 1).
    assert ours["se"] == pytest.approx(reference.bse["year"] * np.sqrt(clusters / (clusters - 1)), rel=1e-4)
    assert ours["beta"] == pytest.approx(reference.params["year"], rel=1e-6)

