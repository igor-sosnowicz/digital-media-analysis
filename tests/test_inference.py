import numpy as np
import pandas as pd
import pytest
from scipy.special import expit

from digital_media_analysis import charts, external, inference, multiverse, power


def trend_data(slope: float, rows: int = 4000, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    year = rng.integers(0, 10, rows)
    group = rng.integers(0, 4, rows)
    p = expit(-1 + 0.3 * group + slope * year)
    return pd.DataFrame({"year": year + 2005, "year_c": year, "group": group, "day": rng.integers(0, 300, rows),
                         "y": (rng.random(rows) < p).astype(int), "weight": 1.0})


def test_tost_shows_equivalence_only_inside_the_bound():
    assert inference.tost(0.0, 0.005, 1.02)["equivalent"]
    assert not inference.tost(0.0, 0.05, 1.02)["equivalent"]
    assert not inference.tost(0.05, 0.005, 1.02)["equivalent"]
    assert inference.per_year_bound(1.25, [2005, 2018]) == pytest.approx(1.25 ** (1 / 13))


def test_fe_logit_matches_statsmodels_and_recovers_the_trend():
    import statsmodels.formula.api as smf

    data = trend_data(0.1)
    table = inference.fe_logit(data, "y", ["year_c"], ["group"], "day")
    reference = smf.logit("y ~ year_c + C(group)", data).fit(disp=False)
    assert table.iloc[0]["beta"] == pytest.approx(reference.params["year_c"], abs=1e-6)
    assert table.iloc[0]["ci_low"] < np.exp(0.1) < table.iloc[0]["ci_high"]


def test_misclassification_correction_recovers_the_true_slope():
    rng = np.random.default_rng(3)
    data = trend_data(0.15, rows=20000, seed=3)
    sensitivity, specificity = 0.8, 0.9
    observed = np.where(data["y"].eq(1), rng.random(len(data)) < sensitivity, rng.random(len(data)) > specificity).astype(int)
    data = data.assign(observed=observed)
    naive = inference.fe_logit(data, "observed", ["year_c"], ["group"], "day").iloc[0]["beta"]
    corrected = inference.corrected_trend(data, "observed", "group", "day", 2005, [(sensitivity, specificity)])
    # Misclassification pulls the slope towards zero; the correction brings it back.
    assert abs(naive) < 0.13 and corrected["beta"] == pytest.approx(0.15, abs=0.03)
    draws = inference.error_rate_draws(80, 20, 90, 10, 20, seed=1)
    assert draws[0] == (0.8, 0.9) and len(draws) == 21


def test_within_author_trend_ignores_differences_between_authors():
    rng = np.random.default_rng(5)
    rows = []
    for author in range(400):
        level = rng.normal(0, 1.5)
        for year in rng.choice(np.arange(2005, 2019), 6, replace=False):
            rows.append({"author": author, "year": year, "y": int(rng.random() < expit(level + 0.1 * (year - 2005)))})
    result = inference.within_author_trend(pd.DataFrame(rows), "y", "author", 2005, "increase")
    assert result["ci_low"] < np.exp(0.1) < result["ci_high"] and result["p_one_sided"] < 0.05


def test_rate_trend_and_survival_and_shift_share():
    rng = np.random.default_rng(7)
    panel = pd.DataFrame({"page": np.repeat(np.arange(30), 7), "year_c": np.tile(np.arange(7), 30)})
    panel["links"] = rng.integers(20, 60, len(panel))
    panel["events"] = rng.poisson(panel["links"] * 0.02 * np.exp(0.2 * panel["year_c"]))
    result = inference.rate_trend(panel, "events", "links", ["year_c"], "page", "page", "increase", "year_c")
    assert result["ci_low"] < np.exp(0.2) < result["ci_high"]

    links = pd.DataFrame({"days": np.r_[rng.exponential(30, 80), rng.exponential(300, 80)], "censored": rng.random(160) < 0.2,
                          "type": ["alt"] * 80 + ["other"] * 80})
    curves, comparison = inference.survival(links, "days", "censored", "type")
    assert set(curves["type"]) == {"alt", "other"} and comparison["p_value"] < 0.001 and comparison["hazard_ratio"] < 1

    shares = pd.DataFrame({"year": [2005] * 4 + [2018] * 4, "group": ["a", "a", "b", "b"] * 2, "weight": [3, 3, 1, 1, 1, 1, 3, 3],
                           "y": [0, 0, 1, 1, 0, 0, 1, 1]})
    parts = inference.shift_share(shares, "y", "group", [2005, 2005], [2018, 2018])
    # Shares within groups do not change; the rise comes from group b growing.
    assert parts["within"] == pytest.approx(0) and parts["composition"] == pytest.approx(parts["total"]) and parts["total"] == pytest.approx(0.5)


def test_power_simulation_and_multiverse():
    strong = power.simulate(4, 10, 100, 0.2, 1.3, replicates=20)
    assert strong["power"] > 0.9
    null = power.simulate(4, 10, 200, 0.2, 1.0, equivalence_odds_ratio=1.2, replicates=20)
    assert null["power_equivalence"] > 0.8
    table = multiverse.run({"a": [1, 2], "b": ["x", "y"]}, lambda choice: {"estimate": choice["a"] * 1.0, "p_one_sided": 0.01 if choice["b"] == "x" else 0.5,
                                                                            "ci_low": 0.5, "ci_high": 2.5})
    assert len(table) == 4 and multiverse.summary(table)["share_significant"] == 0.5
    failing = multiverse.run({"a": [1]}, lambda choice: 1 / 0)
    assert failing["error"].iloc[0].startswith("ZeroDivisionError")


def test_external_comparison(tmp_path):
    path = tmp_path / "gss.csv"
    rows = [{"year": year, "response": response, "count": count}
            for year, great in [(2006, 40), (2008, 38), (2010, 36), (2012, 35)]
            for response, count in [("A great deal", great), ("Only some", 50), ("Hardly any", 100 - great - 50), ("IAP", 5)]]
    pd.DataFrame(rows).to_csv(path, index=False)
    survey = external.load_gss(path)
    assert survey["great_deal"].iloc[0] == pytest.approx(0.40)
    yearly = pd.DataFrame({"year": [2006, 2008, 2010, 2012], "share": [0.10, 0.12, 0.13, 0.16]})
    result = external.compare(yearly, survey, "share", "great_deal")
    assert result["years"] == 4 and result["spearman"] == pytest.approx(-1.0)


def test_charts_draw(tmp_path):
    forest = pd.DataFrame({"label": ["a", "b"], "estimate": [1.1, 0.9], "ci_low": [0.9, 0.8], "ci_high": [1.3, 1.0], "section": ["H1", "H2"]})
    charts.forest(forest, "label", "estimate", "ci_low", "ci_high", bound=1.05, section="section", path=tmp_path / "forest.png")
    curve = pd.DataFrame({"estimate": [1.1, 0.9, 1.2], "ci_low": [1.0, 0.8, 1.1], "ci_high": [1.2, 1.0, 1.3], "p_one_sided": [0.01, 0.6, 0.02],
                          "x": ["a", "b", "a"], "y": [0, 0, 1]})
    charts.specification_curve(curve, ["x", "y"], path=tmp_path / "curve.png")
    yearly = pd.DataFrame({"year": [2005, 2006] * 2, "group": ["a", "a", "b", "b"], "share": [0.1, 0.2, 0.3, 0.2],
                           "low": [0.05, 0.1, 0.2, 0.1], "high": [0.2, 0.3, 0.4, 0.3], "weight": [1, 2, 3, 4]})
    charts.yearly_panels(yearly, "group", path=tmp_path / "panels.png")
    charts.composition(yearly, "year", "group", "weight", path=tmp_path / "composition.png")
    charts.lines(yearly, "year", "group", "share", "low", "high", marker=2005.5, marker_label="x", path=tmp_path / "lines.png")
    charts.stacked_bars(yearly, "year", "group", "weight", path=tmp_path / "bars.png")
    charts.columns(yearly[yearly["group"].eq("a")], "year", "weight", "n", marker=2005.5, path=tmp_path / "columns.png")
    charts.decomposition(pd.DataFrame([{"outcome": "y", "total": 0.1, "within": 0.02, "composition": 0.08}]), "outcome", path=tmp_path / "dec.png")
    charts.heatmap(pd.DataFrame([[0.1, 0.2], [0.0, np.nan]], index=["p", "q"], columns=[2020, 2021]), path=tmp_path / "heat.png")
    charts.labelled_scatter(yearly, "share", "weight", "year", "x", "y", path=tmp_path / "scatter.png")
    events = pd.DataFrame({"timestamp": ["2020-01-01", "2021-05-01"], "title": ["A", "B"], "owner_type": ["influencer", "anonymous"]})
    charts.event_timeline(events, "timestamp", "title", "owner_type", path=tmp_path / "timeline.png")
    curves = pd.DataFrame({"type": ["a"] * 3, "time": [0, 10, 20], "survival": [1, 0.8, 0.5], "low": [1, 0.7, 0.4], "high": [1, 0.9, 0.6]})
    charts.survival_curves(curves, "type", path=tmp_path / "survival.png")
    charts.power_curves(pd.DataFrame({"n": [10, 20], "power": [0.3, 0.9], "power_equivalence": [0.1, 0.7]}), "n", planned=15,
                        path=tmp_path / "power.png")
    assert len(list(tmp_path.glob("*.png"))) == 13
