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


def test_unmeasured_source_types_get_no_set_metrics():
    edit_only = predictions().assign(cites_source=pd.NA, source_types=pd.NA, edit_about_sources=1)
    frame = validation.paired(reference(), edit_only, MANIFEST)
    values = validation.metrics(frame, ["media"])
    assert ("source_types", "masi") not in values and ("cites_source", "f1") not in values
    assert np.isnan(validation.objective(reference(), edit_only, MANIFEST, ["media"])["masi"])
    assert validation.confusion(reference(), edit_only, MANIFEST, "x").empty


def test_weighted_shares_pool_the_splits_of_each_stratum():
    labels = pd.concat([reference(), pd.DataFrame({
        "unit_id": ["e", "f"], "platform": "reddit", "annotator": "IS", "cites_source": [0, 0],
        "source_types": ["none", "none"], "edit_about_sources": pd.array([pd.NA] * 2, dtype="Int64"),
    })], ignore_index=True)
    shares = validation.weighted_shares(labels, MANIFEST, ["media", "none"], samples=100).set_index("variable")
    # Stratum 2010: a, b, e, f (100 / 4 each, two citing); 2011: c, d (40 / 2 each, one citing).
    assert shares.loc["cites_source", "share"] == pytest.approx((25 + 25 + 20) / 140)
    assert shares.loc["media", "share"] == pytest.approx(50 / 140)
    assert "none" not in shares.index
    assert shares.loc["media", "low"] <= shares.loc["media", "share"] <= shares.loc["media", "high"]


def test_weighted_share_by_year_weights_each_stratum_and_pools_the_years():
    manifest = pd.DataFrame({
        "unit_id": ["u1", "u2", "u3", "u4", "r1"], "platform": ["wikipedia"] * 4 + ["reddit"],
        "stratum": ["2020|other", "2020|other", "2021|link", "2021|link", "2020"], "N_h": [10, 10, 2, 2, 5],
        "year": [2020, 2020, 2021, 2021, 2020],
    })
    labels = pd.DataFrame({
        "unit_id": ["u1", "u2", "u3", "u4", "r1"], "platform": ["wikipedia"] * 4 + ["reddit"],
        "source_types": ["personal", "media", "social_blog;unknown", "unknown", "personal"],
    })
    shares = validation.weighted_share_by_year(labels, manifest, "wikipedia", ["social_blog", "unknown", "personal"],
                                               samples=100).set_index("year")
    # Weights: 10 / 2 in 2020 (u1 cites, u2 not), 2 / 2 in 2021 (both cite); the Reddit unit is left out.
    assert shares.loc[2020, "share"] == pytest.approx(0.5) and shares.loc[2021, "share"] == pytest.approx(1.0)
    assert shares.loc["all", "share"] == pytest.approx(7 / 12)
    assert shares.loc["all", ["positives", "units"]].tolist() == [3, 4]
    assert shares.loc["all", "low"] <= shares.loc["all", "share"] <= shares.loc["all", "high"]


def test_differential_errors_rate_per_group_with_a_permutation_test():
    frame = pd.DataFrame({
        "platform": "reddit", "stratum": "s", "weight": 1.0,
        "cites_source": [0] * 20 + [1] * 20,
        "cites_source_pred": [1] * 8 + [0] * 2 + [0] * 10 + [1] * 20,
        "period": (["early"] * 10 + ["late"] * 10) + (["early"] * 10 + ["late"] * 10),
    })
    table = validation.differential_errors(frame, "period", samples=50, permutations=500)
    fp = table[table["rate"].eq("false_positive_rate")].set_index("group")
    assert fp.loc["early", "value"] == pytest.approx(0.8) and fp.loc["late", "value"] == 0.0
    assert fp["p_permutation"].iloc[0] < 0.01
    fn = table[table["rate"].eq("false_negative_rate")]
    # No false negatives at all: nothing to compare.
    assert fn["value"].eq(0).all() and fn["p_permutation"].isna().all()


def test_mcnemar_counts_discordant_pairs():
    frame = pd.DataFrame({"cites_source": [1] * 10, "a": [1] * 10, "b": [0] * 8 + [1] * 2})
    result = validation.mcnemar(frame, "a", "b")
    assert (result["only_first_right"], result["only_second_right"], result["both_right"]) == (8, 0, 2)
    assert result["p_exact"] == pytest.approx(2 * 0.5**8)


def test_ranking_agreement_compares_category_orders():
    shares = pd.DataFrame({
        "platform": "reddit", "variable": ["media", "scientific", "social_blog"] * 3,
        "source": ["gold"] * 3 + ["same"] * 3 + ["reversed"] * 3,
        "share": [0.5, 0.3, 0.1, 0.6, 0.2, 0.1, 0.1, 0.3, 0.5],
    })
    table = validation.ranking_agreement(shares).set_index("source")
    assert table.loc["same", "kendall_tau"] == pytest.approx(1.0) and table.loc["same", "same_top_category"]
    assert table.loc["reversed", "kendall_tau"] == pytest.approx(-1.0) and not table.loc["reversed", "same_top_category"]
