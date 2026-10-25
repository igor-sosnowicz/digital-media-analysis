import pandas as pd
import pytest

from digital_media_analysis import audit


def sample_and_reference() -> tuple[pd.DataFrame, pd.DataFrame]:
    sample = pd.DataFrame({
        "unit_id": ["u1", "u2", "u3", "u4"],
        "source_types": ["scientific", "scientific", "none", "media"],
        "stratum": ["scientific", "scientific", "rest", "rest"],
        "inclusion": [0.5, 0.5, 0.25, 0.25],
    })
    reference = pd.DataFrame({"unit_id": ["u1", "u2", "u3", "u4"], "platform": "reddit",
                              "source_types": ["scientific", "media", "scientific", "media"]})
    return sample, reference


def test_audit_rates_weight_posts_by_inverse_inclusion():
    frame = audit.audit_frame(*sample_and_reference())
    assert frame["weight"].tolist() == [2.0, 2.0, 4.0, 4.0]
    result = audit.rates(frame, ["scientific", "institutional"], samples=200)
    # Weighted: TP 2 of positives 2 + 4; TN 4 of negatives 2 + 4.
    assert result["sensitivity"] == pytest.approx(1 / 3)
    assert result["specificity"] == pytest.approx(2 / 3)
    assert result["youden"] == pytest.approx(0) and not result["valid"]
    assert result["sensitivity_low"] <= result["sensitivity"] <= result["sensitivity_high"]


def test_pooled_rescales_each_source_to_its_size():
    first = pd.DataFrame({"unit_id": ["a", "b"], "source": "audit", "stratum": "s", "weight": [1.0, 3.0],
                          "source_types": "none", "source_types_pred": "none"})
    second = first.assign(source="gold_test", weight=[10.0, 10.0])
    pooled = audit.pooled([first, second])
    assert pooled["weight"].tolist() == [0.5, 1.5, 1.0, 1.0]
    assert pooled["source"].eq("pooled").all()


def test_corrected_shares_apply_rogan_gladen_to_the_share_and_its_bounds():
    yearly = pd.DataFrame({"hypothesis": "H1-B", "outcome": ["consensus", "alternative"], "year": 2010,
                           "share": [0.5, 0.4], "low": [0.4, 0.3], "high": [0.6, 0.5], "group": "all"})
    table = pd.DataFrame({"source": "pooled", "indicator": ["consensus", "alternative"],
                          "sensitivity": [0.9, 0.5], "specificity": [0.8, 0.5]})
    corrected = audit.corrected_shares(yearly, table)
    assert corrected["corrected_share"].iloc[0] == pytest.approx((0.5 + 0.8 - 1) / 0.7)
    assert corrected["corrected_low"].iloc[0] < corrected["corrected_share"].iloc[0] < corrected["corrected_high"].iloc[0]
    # J = 0: the instrument carries no information, so there is no correction.
    assert pd.isna(corrected["corrected_share"].iloc[1])
