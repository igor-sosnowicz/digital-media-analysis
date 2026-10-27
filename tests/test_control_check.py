import pandas as pd
import pytest

from digital_media_analysis import control_check as cc


def _stance_rows() -> pd.DataFrame:
    labels = ["challenges"] * 4 + ["neutral"] * 10 + ["not_applicable"] * 10
    return pd.DataFrame({
        "unit_id": [f"u{i}" for i in range(24)], "label": labels,
        "split": ["test", "test", "dev", "test"] + ["dev"] * 20,
        "decided_by": ["human"] * 23 + ["auto"],
    })


def test_draw_stance_takes_every_test_challenge_and_weights_the_rest():
    sample = cc.draw_stance(_stance_rows(), size=8, seed=1)
    certain = sample[sample["stratum"].eq(cc.CERTAIN)]
    assert sorted(certain["unit_id"]) == ["u0", "u1", "u3"]
    assert certain["weight"].eq(1).all()
    rest = sample[sample["stratum"].eq("rest")]
    assert len(rest) == 5 and "u23" not in set(sample["unit_id"])
    assert rest["weight"].iloc[0] == pytest.approx(20 / 5)


def test_human_consensus_keeps_identical_reddit_sets_only():
    first = pd.DataFrame({"unit_id": ["a", "b", "c", "d"], "platform": ["reddit"] * 3 + ["wikipedia"],
                          "source_types": ["media;other", "media", "none", "media"]})
    second = pd.DataFrame({"unit_id": ["a", "b", "c", "d"], "platform": ["reddit"] * 3 + ["wikipedia"],
                           "source_types": ["other; media", "social_blog", "none", "media"]})
    assert list(cc.human_consensus(first, second)["unit_id"]) == ["a", "c"]


def test_blind_hides_labels_and_shuffles():
    sample = cc.draw_stance(_stance_rows(), size=8, seed=1).assign(subreddit="s", title="t", text="", link="")
    blind = cc.blind(sample, "stance")
    assert "label" not in blind.columns and "stratum" not in blind.columns
    assert set(blind["unit_id"]) == set(sample["unit_id"])


def test_kappa_and_scores():
    first = pd.Series(["a", "a", "b", "b"])
    assert cc.cohen_kappa(first, first) == pytest.approx(1.0)
    assert cc.cohen_kappa(first, pd.Series(["a", "b", "a", "b"])) == pytest.approx(0.0)
    frame = pd.DataFrame({"unit_id": ["1", "2"], "label": ["media;other", "none"], "blind": ["media", "none"]})
    scores = {row["measure"]: row["value"] for row in cc.score_sets(frame, "audit")}
    assert scores["exact_set"] == 0.5 and scores["jaccard_mean"] == pytest.approx(0.75)
    assert scores["cites_source_agreement"] == 1.0
    assert list(cc.disagreements(frame, "audit", multilabel=True)["unit_id"]) == ["1"]
