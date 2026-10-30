import numpy as np
import pandas as pd
import pytest

from digital_media_analysis import robustness


def two_by_two(a: int, b: int, c: int, d: int) -> tuple[np.ndarray, np.ndarray]:
    """Rows for a 2x2 table: x = 1 has a events and b non-events, x = 0 has c events and d non-events."""
    x = np.array([1] * (a + b) + [0] * (c + d), dtype=float)
    y = np.array([1] * a + [0] * b + [1] * c + [0] * d, dtype=float)
    return np.column_stack([np.ones_like(x), x]), y


def test_firth_matches_the_closed_form_for_a_two_by_two_table():
    # Firth's estimate of the log odds ratio adds 0.5 to every cell.
    x, y = two_by_two(3, 40, 1, 60)
    beta, _, _ = robustness.firth_logit(x, y)
    assert beta[1] == pytest.approx(np.log((3.5 * 60.5) / (40.5 * 1.5)), abs=1e-6)


def test_firth_stays_finite_under_separation():
    x, y = two_by_two(5, 0, 0, 5)
    beta, covariance, loglik = robustness.firth_logit(x, y)
    assert np.isfinite(beta).all() and np.isfinite(loglik)
    assert beta[1] == pytest.approx(np.log((5.5 * 5.5) / (0.5 * 0.5)), abs=1e-5)


def rising_events(slope: float, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for page, offset in [("A", -3.0), ("B", -4.0)]:
        for year in range(2020, 2027):
            probability = 1 / (1 + np.exp(-(offset + slope * (year - 2020))))
            rows += [{"page": page, "year": year, "revision": f"{page}{year}-{i // 5}", "event": int(rng.random() < probability)}
                     for i in range(200)]
    return pd.DataFrame(rows)


def test_firth_trend_tests_the_direction_with_penalised_lr():
    data = rising_events(0.3)
    up = robustness.firth_trend(data, "event", "page", "increase", 2020)
    assert up["odds_ratio_per_year"] > 1 and up["p_one_sided"] < 0.01 and up["lr_statistic"] > 0
    down = robustness.firth_trend(data, "event", "page", "decrease", 2020)
    assert down["p_one_sided"] > 0.99
    # A page without any event stays in the model.
    with_empty = pd.concat([data, pd.DataFrame({"page": "C", "year": [2021, 2022], "revision": ["c1", "c2"], "event": 0})])
    assert np.isfinite(robustness.firth_trend(with_empty, "event", "page", "increase", 2020)["beta"])


def test_firth_interval_agrees_with_its_test():
    # Few events, as in H2: the interval excludes no change exactly when the two-sided test rejects it.
    for slope, seed in [(0.3, 0), (0.15, 1), (0.05, 2)]:
        data = rising_events(slope, seed)
        data = data[data["year"].ge(2023) | data.index.isin(data.index[::7])]
        result = robustness.firth_trend(data, "event", "page", "increase", 2020)
        two_sided = 2 * min(result["p_one_sided"], 1 - result["p_one_sided"])
        assert result["ci_low"] < result["odds_ratio_per_year"] < result["ci_high"]
        assert (result["ci_low"] > 1 or result["ci_high"] < 1) == (two_sided < 0.05)


def test_firth_fit_with_a_fixed_coefficient_profiles_the_likelihood():
    x, y = two_by_two(3, 40, 1, 60)
    beta, _, loglik = robustness.firth_logit(x, y)
    _, _, at_estimate = robustness.firth_logit(x, y, fixed={1: beta[1]})
    fixed_beta, _, at_zero = robustness.firth_logit(x, y, fixed={1: 0.0})
    assert at_estimate == pytest.approx(loglik, abs=1e-8)
    assert fixed_beta[1] == 0.0 and at_zero < loglik


def test_exact_year_sum_test_counts_equally_likely_sets():
    # Pairs of 2020-2023 sum to 4041, 4042, 4043, 4043, 4044, 4045; only one reaches 2022 + 2023.
    assert robustness.exact_year_sum_test([2020, 2021, 2022, 2023], [2022, 2023]) == pytest.approx(1 / 6)
    assert robustness.exact_year_sum_test([2020, 2021, 2022, 2023], [2020, 2021]) == 1.0


def test_permutation_trend_shuffles_years_between_revisions_within_pages():
    data = rising_events(0.4)
    def slope(frame: pd.DataFrame) -> float:
        return float(np.polyfit(frame["year"], frame["event"], 1)[0])

    result = robustness.permutation_trend(data, slope, "revision", "page", permutations=200, seed=1)
    assert result["p_one_sided"] < 0.05
    assert robustness.permutation_trend(data, slope, "revision", "page", permutations=200, seed=1) == result
    flat = data.assign(event=np.random.default_rng(3).random(len(data)) < 0.05)
    assert robustness.permutation_trend(flat, slope, "revision", "page", permutations=200, seed=1)["p_one_sided"] > 0.05


def test_revision_counts_and_poisson_trend():
    links = pd.DataFrame({"page": "A", "revision": ["r1", "r1", "r2", "r3"], "year": [2020, 2020, 2021, 2022],
                          "alternative": [1, 0, 0, 1]})
    revisions = robustness.revision_counts(links, "alternative")
    assert revisions[["revision", "links", "events", "any_event"]].values.tolist() == [["r1", 2, 1, 1], ["r2", 1, 0, 0], ["r3", 1, 1, 1]]
    data = rising_events(0.3)
    counts = robustness.revision_counts(data, "event")
    result = robustness.poisson_trend(counts, "page", "increase", 2020)
    assert result["rate_ratio_per_year"] > 1 and result["p_one_sided"] < 0.01


def test_leave_one_out_refits_without_each_row():
    data = pd.DataFrame({"value": [1, 2, 3]})
    table = robustness.leave_one_out(data, "value", lambda frame: {"total": int(frame["value"].sum())}, [0, 2])
    assert table[["dropped", "total"]].values.tolist() == [[0, 5], [2, 3]]
