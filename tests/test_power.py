import numpy as np
import pytest

from digital_media_analysis import power

SLOPE = np.log(1.25) / 13  # H1 SESOI per year (2005-2018)


def test_planning_formula_matches_the_simulation_with_and_without_instrument_error():
    for share, units, sensitivity, specificity in ((0.15, 7_000, 1.0, 1.0), (0.10, 21_000, 0.6, 0.97)):
        simulated = power.simulate(1, 14, units // 14, share, float(np.exp(SLOPE)), intercept_sd=0.0, replicates=120,
                                   fixed_effects=False, sensitivity=sensitivity, specificity=specificity)["power"]
        assert simulated == pytest.approx(power.trend_power(units, share, SLOPE, 14, sensitivity, specificity), abs=0.1)


def test_instrument_error_clustering_and_equivalence_cost_units():
    perfect = power.units_needed(0.10, SLOPE, 14)
    assert power.units_needed(0.10, SLOPE, 14, design_effect=2.0) == pytest.approx(2 * perfect, rel=0.01)
    assert power.units_needed(0.10, SLOPE, 14, 0.7, 0.98) > 1.5 * perfect
    assert power.units_needed(0.10, SLOPE, 14, equivalence=True) > perfect
    assert power.trend_power(perfect, 0.10, SLOPE, 14) == pytest.approx(0.8, abs=0.01)
    assert power.equivalence_power(10, 0.10, SLOPE, 14) == 0.0


def test_observed_share_and_year_variance():
    assert power.observed_share(0.1, 0.7, 0.98) == pytest.approx(0.07 + 0.018)
    assert power.year_variance(14) == pytest.approx(16.25)


def test_other_planning_tests():
    assert power.binomial_power(30, 0.5, 0.25) == pytest.approx(0.819, abs=0.001)
    assert power.binomial_power(30, 0.25, 0.25) <= 0.05
    assert power.events_needed(0.434, 1.25) == 506
    assert power.bound_power(4_000, 0.0075, 0.02, 3.0) > 0.99
    assert power.two_share_power(0.5, 0.5, 1_000, 1_000) == pytest.approx(0.05)


def test_design_effect_of_independent_and_identical_clusters():
    clusters = np.repeat(np.arange(50), 10)
    independent = power.design_effect(np.random.default_rng(1).random(500) < 0.4, clusters)
    assert independent["design_effect"] == pytest.approx(1.0, abs=0.3)
    identical = power.design_effect(np.repeat(np.random.default_rng(2).random(50) < 0.4, 10), clusters)
    assert identical["icc"] == pytest.approx(1.0, abs=0.01)
    assert identical["design_effect"] == pytest.approx(10.0, abs=0.1)
