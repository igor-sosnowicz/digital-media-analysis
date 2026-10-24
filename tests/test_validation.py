import numpy as np
import pandas as pd
import pytest

from digital_media_analysis import annotations, validation

MANIFEST = pd.DataFrame({
    "unit_id": ["a", "b", "c", "d", "e", "f"],
    "platform": "reddit",
    "split": ["dev", "dev", "dev", "dev", "test", "test"],
    "stratum": ["2010", "2010", "2011", "2011", "2010", "2010"],
    "N_h": [100, 100, 40, 40, 100, 100],
})


def reference() -> pd.DataFrame:
    return pd.DataFrame({
        "unit_id": ["a", "b", "c", "d"],
        "platform": "reddit",
        "annotator": ["IS", "IS", "JP", "JP"],
        "cites_source": [1, 1, 0, 1],
        "source_types": ["media", "media;scientific", "none", "social_blog"],
        "edit_about_sources": pd.array([pd.NA] * 4, dtype="Int64"),
    })


def predictions() -> pd.DataFrame:
    return pd.DataFrame({
        "unit_id": ["a", "b", "c", "d"],
        "platform": "reddit",
        "cites_source": [1, 1, 1, 0],
        "source_types": ["media", "media", "other", "none"],
        "edit_about_sources": pd.NA,
    })


def test_design_weights_use_the_coded_units_of_each_stratum():
    weights = validation.design_weights(reference(), MANIFEST)
    # Two coded units in each dev stratum: 100 / 2 and 40 / 2.
    assert weights.set_index("unit_id")["weight"].to_dict() == {"a": 50.0, "b": 50.0, "c": 20.0, "d": 20.0}


def test_design_weights_reject_units_outside_the_manifest():
    with pytest.raises(ValueError, match="not in the manifest"):
        validation.design_weights(pd.DataFrame({"unit_id": ["zz"], "platform": ["reddit"]}), MANIFEST)


def test_metrics_are_weighted():
    frame = validation.paired(reference(), predictions(), MANIFEST)
    values = validation.metrics(frame, ["media", "scientific", "social_blog", "other"])
    # cites_source: TP a, b (50 + 50), FP c (20), FN d (20).
    assert values[("cites_source", "precision")] == pytest.approx(100 / 120)
    assert values[("cites_source", "recall")] == pytest.approx(100 / 120)
    assert values[("source_types:media", "f1")] == 1.0
    assert values[("source_types:scientific", "recall")] == 0.0
    assert np.isnan(values[("source_types:other", "recall")])
    # MASI: a 1, b 2/3 x 1/2 (subset), c 0, d 0, weighted 50, 50, 20, 20.
    assert values[("source_types", "masi")] == pytest.approx((50 * 1 + 50 * (1 - (1 - 0.5 * 2 / 3))) / 140)
    assert ("edit_about_sources", "f1") not in values


def test_evaluate_reports_subsets_support_and_intervals():
    table = validation.evaluate(reference(), predictions(), MANIFEST, "fake", ["media", "scientific", "none"], samples=50)
    assert set(table["subset"]) == {"all", "IS", "JP"}
    media = table[(table["subset"] == "all") & (table["variable"] == "source_types:media") & (table["metric"] == "f1")].iloc[0]
    assert media["support"] == 2 and media["note"] == validation.TOO_FEW
    cites = table[(table["subset"] == "all") & (table["variable"] == "cites_source") & (table["metric"] == "f1")].iloc[0]
    assert cites["low"] <= cites["value"] <= cites["high"]
    assert "source_types:none" not in set(table["variable"])
    # Same seed, same intervals.
    again = validation.evaluate(reference(), predictions(), MANIFEST, "fake", ["media", "scientific", "none"], samples=50)
    pd.testing.assert_frame_equal(table, again)


def test_nominal_metrics():
    truth = pd.Series(["a", "a", "b", "c"])
    predicted = pd.Series(["a", "b", "b", "c"])
    values = validation.nominal_metrics(truth, predicted, pd.Series([1.0, 1.0, 1.0, 1.0]), ["a", "b", "c"])
    assert values["accuracy"] == 0.75
    assert values["a:recall"] == 0.5 and values["b:precision"] == 0.5
    assert values["macro_f1"] == pytest.approx(np.mean([2 / 3, 2 / 3, 1.0]))


def test_confusion_counts():
    counts = validation.confusion(reference(), predictions(), MANIFEST, "fake").iloc[0]
    assert (counts["tp"], counts["fp"], counts["fn"], counts["tn"]) == (2, 1, 1, 0)


def test_gold_reference_keeps_agreeing_units_and_sets_conflicts_aside():
    labels = pd.DataFrame({
        "unit_id": ["a", "b", "b", "c", "c"],
        "platform": "reddit",
        "annotator": ["IS", "IS", "JP", "IS", "JP"],
        "cites_source": pd.array([1, 1, 1, 1, 0], dtype="Int64"),
        "source_types": ["media", "media", "media", "media", "none"],
        "edit_about_sources": pd.array([pd.NA] * 5, dtype="Int64"),
    })
    reference_labels, conflicts = annotations.gold_reference(labels)
    assert sorted(reference_labels["unit_id"]) == ["a", "b"]
    assert sorted(conflicts["unit_id"].unique()) == ["c"]
