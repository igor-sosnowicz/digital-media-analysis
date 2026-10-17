import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import cohen_kappa_score

from digital_media_analysis import agreement
from digital_media_analysis.agreement import Estimate, cohen_kappa, krippendorff_alpha, masi_distance

N = None
# Krippendorff (2011), "Computing Krippendorff's Alpha-Reliability": 4 observers, 12 units.
KRIPPENDORFF_EXAMPLE = [
    [1, 2, 3, 3, 2, 1, 4, 1, 2, N, N, N],
    [1, 2, 3, 3, 2, 2, 4, 1, 2, 5, N, 3],
    [N, 3, 3, 3, 2, 3, 4, 2, 2, 5, 1, N],
    [1, 2, 3, 3, 2, 4, 4, 1, 2, 5, 1, N],
]


def test_alpha_matches_krippendorff_reference_example():
    units = list(zip(*KRIPPENDORFF_EXAMPLE))
    assert round(krippendorff_alpha(units, samples=0).value, 3) == 0.743


def test_alpha_is_one_for_perfect_agreement_and_undefined_without_variation():
    assert krippendorff_alpha([[1, 1], [0, 0], [1, 1]], samples=0).value == 1.0
    assert np.isnan(krippendorff_alpha([[1, 1], [1, 1]], samples=0).value)
    assert np.isnan(krippendorff_alpha([[1, None], [0, None]], samples=0).value)


def test_kappa_matches_sklearn():
    rng = np.random.default_rng(0)
    first = rng.integers(0, 3, 300)
    second = np.where(rng.random(300) < 0.7, first, rng.integers(0, 3, 300))
    expected = cohen_kappa_score(first, second)
    assert cohen_kappa(first.tolist(), second.tolist(), samples=0).value == pytest.approx(expected)


def test_kappa_skips_units_missing_a_label():
    assert cohen_kappa([1, 0, 1, None], [1, 0, 1, 0], samples=0).value == 1.0


def test_bootstrap_interval_is_deterministic_and_contains_estimate():
    units = list(zip(*KRIPPENDORFF_EXAMPLE))
    first = krippendorff_alpha(units, samples=500, seed=7)
    assert first == krippendorff_alpha(units, samples=500, seed=7)
    assert first.low <= first.value <= first.high


@pytest.mark.parametrize(
    ("first", "second", "distance"),
    [
        ("ab", "ab", 0.0),
        ("", "", 0.0),
        ("ab", "a", 1 - 1 / 2 * 2 / 3),
        ("ab", "bc", 1 - 1 / 3 * 1 / 3),
        ("a", "b", 1.0),
        ("", "a", 1.0),
    ],
)
def test_masi_distance(first, second, distance):
    assert masi_distance(frozenset(first), frozenset(second)) == pytest.approx(distance)


def make_labels(rows: list[tuple]) -> pd.DataFrame:
    labels = pd.DataFrame(rows, columns=["unit_id", "platform", "annotator", "cites_source", "source_types", "edit_about_sources", "uncertain"])
    for column in ["cites_source", "edit_about_sources", "uncertain"]:
        labels[column] = labels[column].astype("Int64")
    return labels


@pytest.fixture
def labels() -> pd.DataFrame:
    return make_labels([
        ("r1", "reddit", "A", 1, "media", None, 0),
        ("r1", "reddit", "B", 1, "media", None, 0),
        ("r2", "reddit", "A", 1, "media;nauka", None, 0),
        ("r2", "reddit", "B", 1, "nauka", None, 1),
        ("r3", "reddit", "A", 0, "", None, 0),
        ("r3", "reddit", "B", 1, "niesprecyzowane", None, 0),
        ("r4", "reddit", "A", 0, "", None, 0),
        ("r4", "reddit", "B", 0, "", None, 0),
        ("w1", "wikipedia", "A", 0, "", 1, 0),
        ("w1", "wikipedia", "B", 0, "", 1, 0),
        ("w2", "wikipedia", "A", 1, "oficjalne", 0, 0),
        ("w2", "wikipedia", "B", 1, "oficjalne", 0, 0),
    ])


def test_agreement_table_rows_and_values(labels):
    table = agreement.agreement_table(labels, ["media", "nauka", "oficjalne", "niesprecyzowane", "inne"], samples=0)
    reddit = table[table["platform"].eq("reddit")].set_index("variable")
    assert list(reddit.index[:2]) == ["cites_source", "source_types"]
    assert "edit_about_sources" not in reddit.index
    assert reddit.loc["cites_source", "units"] == 4
    assert reddit.loc["cites_source", "observed_agreement"] == 0.75
    assert reddit.loc["cites_source", "distance"] == "nominal"
    assert reddit.loc["source_types", "distance"] == "MASI"
    assert np.isnan(reddit.loc["source_types", "kappa"])
    assert reddit.loc["source_types:media", "observed_agreement"] == 0.75
    # Nobody used `inne`, so agreement on it is undefined rather than perfect.
    assert np.isnan(reddit.loc["source_types:inne", "alpha"])
    assert reddit.loc["source_types:inne", "positive_units"] == 0
    # `media` agrees perfectly on two units only: reported, but not judged reliable.
    assert reddit.loc["source_types:media", "positive_units"] == 2
    assert reddit.loc["source_types:media", "verdict"] == "za mało przypadków"
    assert reddit.loc["source_types", "positive_units"] == 3
    wikipedia = table[table["platform"].eq("wikipedia")].set_index("variable")
    assert wikipedia.loc["edit_about_sources", "alpha"] == 1.0


def test_disagreements_list_only_differing_units(labels):
    table = agreement.disagreements(labels)
    assert table[["unit_id", "variable", "A", "B"]].values.tolist() == [
        ["r3", "cites_source", "0", "1"],
        ["r2", "source_types", "media;nauka", "nauka"],
        ["r3", "source_types", "(brak)", "niesprecyzowane"],
    ]
    assert table.set_index(["unit_id", "variable"]).loc[("r2", "source_types"), "uncertain"] == "B"


def test_annotator_summary(labels):
    summary = agreement.annotator_summary(labels).loc["reddit"]
    assert summary.loc["A", "cites_share"] == 0.5
    assert summary.loc["B", "uncertain_share"] == 0.25
    assert summary.loc["A", "mean_types_when_citing"] == 1.5


@pytest.mark.parametrize(
    ("estimate", "expected"),
    [
        (Estimate(0.9, 0.82, 0.97), "rzetelne"),
        (Estimate(0.85, 0.6, 0.95), "rzetelne punktowo, przedział niepewny"),
        (Estimate(0.7), "tylko wstępne wnioski"),
        (Estimate(0.4, 0.1, 0.6), "niewystarczające"),
        (Estimate(np.nan), "brak zmienności"),
    ],
)
def test_verdict(estimate, expected):
    assert agreement.verdict(estimate) == expected
    assert agreement.verdict(estimate, positive_units=4) == "za mało przypadków"
    assert agreement.verdict(estimate, positive_units=5) == expected
