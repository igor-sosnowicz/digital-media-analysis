"""Tests for scripts/07_kappa_consensus.py (kappa per pair and consensus cases)."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import cohen_kappa_score

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "07_kappa_consensus.py"
spec = importlib.util.spec_from_file_location("kappa_consensus", SCRIPT)
kappa_consensus = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kappa_consensus)

CATEGORY_CODES = ["scientific", "institutional", "media", "personal", "social_blog",
                  "encyclopedia", "other", "unknown", "none"]


def make_labels(rows):
    labels = pd.DataFrame(
        rows,
        columns=["unit_id", "platform", "annotator", "cites_source", "source_types",
                 "edit_about_sources", "uncertain"],
    )
    for column in ["cites_source", "edit_about_sources", "uncertain"]:
        labels[column] = labels[column].astype("Int64")
    return labels


@pytest.fixture
def labels() -> pd.DataFrame:
    return make_labels([
        # identical single label
        ("r1", "reddit", "JP", 1, "media", None, 0),
        ("r1", "reddit", "IS", 1, "media", None, 0),
        # identical multi-code label: agreement, but not a single label
        ("r2", "reddit", "JP", 1, "media;scientific", None, 0),
        ("r2", "reddit", "IS", 1, "media;scientific", None, 0),
        # both `none`: a single label
        ("r3", "reddit", "JP", 0, "", None, 0),
        ("r3", "reddit", "IS", 0, "", None, 0),
        # disagreement
        ("r4", "reddit", "JP", 0, "none", None, 0),
        ("r4", "reddit", "IS", 1, "unknown", None, 0),
        # one annotator missing: skipped everywhere
        ("r5", "reddit", "JP", 1, "media", None, 0),
        ("r5", "reddit", "IS", pd.NA, None, None, pd.NA),
        # wikipedia pair, identical single label
        ("w1", "wikipedia", "JP", 1, "institutional", 0, 0),
        ("w1", "wikipedia", "IS", 1, "institutional", 0, 1),
        # wikipedia pair: edit_about_sources disagreement
        ("w2", "wikipedia", "JP", 1, "media", 1, 0),
        ("w2", "wikipedia", "IS", 1, "media", 0, 0),
        # third annotator only on reddit: IS–MR share one unit
        ("r6", "reddit", "IS", 0, "none", None, 0),
        ("r6", "reddit", "MR", 0, "none", None, 0),
    ])


def test_kappa_rows_and_values(labels):
    table = kappa_consensus.kappa_table(labels, CATEGORY_CODES, samples=0, seed=1)
    reddit = table[table["platform"].eq("reddit") & table["pair"].eq("IS–JP")]
    cites = reddit[reddit["variable"].eq("cites_source")].iloc[0]
    # units r1..r5 minus the missing one: [1, 1, 0, 0] vs [1, 1, 0, 1]
    expected = cohen_kappa_score([1, 1, 0, 0], [1, 1, 0, 1])
    assert cites["units"] == 4
    assert cites["observed_agreement"] == 0.75
    assert cites["kappa"] == pytest.approx(expected)
    assert np.isnan(cites["kappa_low"])  # samples=0 -> no interval
    source_types = reddit[reddit["variable"].eq("source_types")].iloc[0]
    # exact-set kappa: r3 is empty (`""`), r4 JP is `none` vs IS `unknown`
    expected_set = cohen_kappa_score(
        ["media", "media;scientific", "", "none"],
        ["media", "media;scientific", "", "unknown"],
    )
    assert source_types["units"] == 4
    assert source_types["observed_agreement"] == 0.75
    assert source_types["kappa"] == pytest.approx(expected_set)
    # wikipedia pair has edit_about_sources
    wiki = table[table["platform"].eq("wikipedia")]
    assert {"cites_source", "source_types", "source_types:institutional", "edit_about_sources"} <= set(
        wiki["variable"]
    )
    assert wiki[wiki["variable"].eq("edit_about_sources")]["units"].iloc[0] == 2


def test_kappa_skips_pairs_without_shared_units(labels):
    table = kappa_consensus.kappa_table(labels, CATEGORY_CODES, samples=0, seed=1)
    pairs = set(table["pair"])
    assert "IS–JP" in pairs and "IS–MR" in pairs
    assert "JP–MR" not in pairs  # they share no units


def test_consensus_keeps_only_single_label_agreement(labels):
    consensus = kappa_consensus.consensus_cases(labels)
    # r2 agrees on cites_source (both 1) although source_types is multi-code;
    # r4 disagrees on everything, r5 has a missing label
    assert set(consensus["unit_id"]) == {"r1", "r2", "r3", "w1", "w2", "r6"}
    media = consensus[(consensus["unit_id"].eq("r1")) & (consensus["variable"].eq("source_types"))].iloc[0]
    assert media["label"] == "media"
    assert media["value_1"] == "media" and media["value_2"] == "media"
    assert media["pair"] == "IS–JP"
    cite_row = consensus[(consensus["unit_id"].eq("r2")) & (consensus["variable"].eq("cites_source"))].iloc[0]
    assert cite_row["label"] == "1"
    none_case = consensus[(consensus["unit_id"].eq("r3")) & (consensus["variable"].eq("source_types"))].iloc[0]
    assert none_case["label"] == "none"
    assert not consensus["unit_id"].isin(["r4", "r5"]).any()
    # wikipedia: w1 and w2 agree on cites_source and source_types;
    # edit_about_sources is not a primary label variable
    wiki = consensus[consensus["unit_id"].isin(["w1", "w2"])]
    assert set(wiki["variable"]) == {"cites_source", "source_types"}
    assert wiki[wiki["unit_id"].eq("w1")]["uncertain"].iloc[0] == "IS"


def test_empty_labels_give_empty_tables_with_columns():
    empty = make_labels([])
    table = kappa_consensus.kappa_table(empty, CATEGORY_CODES, samples=0, seed=1)
    assert list(table.columns) == kappa_consensus.KAPPA_COLUMNS
    assert len(table) == 0
    consensus = kappa_consensus.consensus_cases(empty)
    assert list(consensus.columns) == kappa_consensus.CONSENSUS_COLUMNS
    assert len(consensus) == 0


def test_coverage_reports_shared_units_over_phase_units(labels):
    manifest = pd.DataFrame({
        "unit_id": ["r1", "r2", "r3", "r4", "r5", "r6", "r7", "w1", "w2"],
        "platform": ["reddit"] * 7 + ["wikipedia"] * 2,
        "phase": ["pilot"] * 9,
    })
    table = kappa_consensus.kappa_table(labels, CATEGORY_CODES, samples=0, seed=1, manifest=manifest)
    reddit = table[table["platform"].eq("reddit") & table["pair"].eq("IS–JP")]
    # manifest has 7 reddit units; only r1-r5 (minus missing r5 for IS) are shared
    cites = reddit[reddit["variable"].eq("cites_source")].iloc[0]
    assert cites["phase_units"] == 7
    assert cites["units"] == 4  # r1-r4 shared, r5 missing for IS
    assert cites["coverage"] == pytest.approx(4 / 7)


def test_main_exits_without_two_annotators(monkeypatch, tmp_path):
    (tmp_path / "labels").mkdir()
    (tmp_path / "labels" / "pilot").mkdir()
    monkeypatch.setattr(kappa_consensus.annotations, "LABELS_DIR", tmp_path / "labels")
    with pytest.raises(SystemExit):
        kappa_consensus.main(argv=["--phase", "pilot"])
