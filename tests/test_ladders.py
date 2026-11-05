import numpy as np
import pandas as pd
import pytest

from digital_media_analysis import ladders


def trend(units, share=0.10, sensitivity=1.0, specificity=1.0, design_effect=2.0, valid=True):
    return {"test": "trend", "valid": valid, "units": units, "share": share, "sensitivity": sensitivity, "specificity": specificity,
            "design_effect": design_effect, "years": 14, "sesoi_period_odds_ratio": 1.25}


def test_gate_takes_the_first_powered_valid_variant_and_keeps_the_rest_secondary():
    variants = {"H1": trend(20_000, sensitivity=0.21, specificity=0.987), "H1-S1": trend(200_000, share=0.36),
                "H1-S2": trend(200_000, share=0.36), "H1-S3": trend(5_000), "H2": trend(4_000, share=0.0015),
                "H2-S1": {**trend(10_000, share=0.49, design_effect=2.9), "years": 7, "sesoi_period_odds_ratio": 1.5},
                "H2-S2": {"test": "two_shares", "valid": True, "share": 0.45, "units_first": 3_000, "units_second": 3_000,
                          "design_effect": 2.9, "sesoi_odds_ratio": 1.5},
                "H2-S4": {"test": "bound", "valid": True, "units": 4_000, "planning_share": 0.0015, "bound": 0.02, "design_effect": 2.9},
                "H2-S3": {"test": "cox", "valid": True, "events": 600, "exposed_share": 0.49, "hazard_ratio": 1.25},
                "H2-S5": {"test": "binomial", "valid": True, "units": 10, "planning_share": 0.5, "null_share": 0.25}}
    decision = ladders.gate(variants)
    assert decision["H1"]["primary"] == "H1-S1"
    assert decision["H1"]["secondary"] == ["H1-S2"]
    assert set(decision["H1"]["descriptive"]) == {"H1", "H1-S3"}
    assert decision["H2"]["primary"] == "H2-S1"
    assert "H2-S3" in decision["H2"]["secondary"] and "H2-S5" in decision["H2"]["descriptive"]
    assert ladders.roles(decision)["H2-S1"] == "primary"


def test_invalid_variant_never_becomes_primary_even_with_power():
    decision = ladders.gate({"H1": trend(10**7, valid=False)}, ladders={"H1": ["H1"]}, secondary_only={})
    assert decision["H1"]["primary"] is None
    assert decision["H1"]["variants"]["H1"]["power"] is None


def test_holm_adjusts_step_down_and_ignores_missing_values():
    adjusted = ladders.holm({"a": 0.01, "b": 0.04, "c": np.nan})
    assert adjusted["a"] == pytest.approx(0.02)
    assert adjusted["b"] == pytest.approx(0.04)
    assert np.isnan(adjusted["c"])


def test_exclusions():
    units = pd.DataFrame({"unit_id": ["p_a", "c_x", "p_b"], "post_id": ["a", "a", "b"]})
    assert ladders.without_v1_posts(units, {"a"})["unit_id"].tolist() == ["p_b"]
    links = pd.DataFrame({"title": ["COVID-19", "Grypa", "Grypa"], "revid": [1, 2, 2], "url": ["u1", "u2", "u3"]})
    assert ladders.without_pages(links, ["COVID-19"])["title"].tolist() == ["Grypa", "Grypa"]
    assert ladders.without_bulk(links, 1)["url"].tolist() == ["u1"]


def test_level_tests():
    rng = np.random.default_rng(3)
    values = pd.Series(rng.random(3_000) < 0.005)
    below = ladders.share_below(values, pd.Series(np.repeat(np.arange(300), 10)), 0.02)
    assert below["p_one_sided"] < 0.001 and below["ci_high"] < 0.02
    above = ladders.share_above(8, 10, 0.25)
    assert above["p_one_sided"] < 0.001 and above["estimate"] == 0.8


def test_attenuated_bound_shrinks_with_instrument_error():
    assert ladders.attenuated_bound(1.5, 0.3, 1.0, 1.0) == pytest.approx(1.5)
    shrunk = ladders.attenuated_bound(1.5, 0.44, 0.81, 0.77)
    assert 1.0 < shrunk < 1.5
