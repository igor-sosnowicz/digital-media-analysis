import json

import numpy as np
import pandas as pd
import pytest

from digital_media_analysis import annotation_sheets, llm_annotation, stance
from digital_media_analysis.codebook import load_codebook
from test_stance import posts


def fake(name: str, answers: dict[str, dict], tmp_path) -> llm_annotation.Annotator:
    """An annotator that answers from a dict keyed by the post title, counting its calls."""
    calls = []

    def ask(system, prompt, schema):
        calls.append(prompt)
        title = next(line.split(": ", 1)[1] for line in prompt.splitlines() if line.startswith("tytuł"))
        return answers.get(title), f"fake-{name}"

    annotator = llm_annotation.Annotator(name, f"fake-{name}", ask, tmp_path)
    annotator.calls = calls
    return annotator


def records() -> list[dict]:
    return posts().rename(columns={"group": "subreddit", "title": "tytuł", "text": "treść"}).to_dict("records")


def test_prompt_comes_from_the_codebook_and_is_deterministic():
    codebook = load_codebook()
    task = llm_annotation.TASKS["stance"]
    prompt = llm_annotation.system_prompt(task, codebook)
    assert prompt == llm_annotation.system_prompt(task, codebook)
    assert all(value in prompt for value in codebook.variable("consensus_stance").values) and "R14" in prompt
    sources = llm_annotation.system_prompt(llm_annotation.TASKS["sources_wikipedia"], codebook)
    assert "edit_about_sources" in sources and "R9" in sources and "R14:" not in sources
    schema = llm_annotation.schema(llm_annotation.TASKS["sources_wikipedia"], codebook)
    assert schema["properties"]["label"]["type"] == "array" and schema["required"][-1] == "edit_about_sources"


def test_normalize_rejects_values_outside_the_codebook():
    codebook = load_codebook()
    sources = llm_annotation.TASKS["sources_reddit"]
    assert llm_annotation.normalize(sources, {"label": ["Media", "scientific"], "confidence": "high", "reason": "x"}, codebook)["label"] == "media;scientific"
    assert llm_annotation.normalize(sources, {"label": ["none", "media"], "confidence": "high", "reason": "x"}, codebook)["label"] == "media"
    assert llm_annotation.normalize(sources, {"label": ["blog"], "confidence": "high", "reason": "x"}, codebook)["label"] is None
    assert llm_annotation.normalize(llm_annotation.TASKS["stance"], None, codebook)["label"] is None


def test_annotator_caches_answers(tmp_path):
    codebook = load_codebook()
    answers = {"Vaccines cause autism, wake up": {"label": "challenges", "confidence": "high", "reason": "R14"}}
    annotator = fake("A1", answers, tmp_path)
    task = llm_annotation.TASKS["stance"]
    first = annotator.annotate(task, records(), ["unit_id"], codebook)
    assert first["label"].iloc[0] == "challenges" and first["label"].iloc[1:].isna().all() and len(annotator.calls) == 3
    again = fake("A1", answers, tmp_path)
    second = again.annotate(task, records(), ["unit_id"], codebook)
    assert again.calls == [] and second["label"].equals(first["label"])
    assert json.loads((tmp_path / "A1.jsonl").read_text(encoding="utf-8").splitlines()[0])["served_by"] == "fake-A1"


def test_rule_flags():
    sources = llm_annotation.TASKS["sources_reddit"]
    assert llm_annotation.rule_flags(sources, {"tytuł": "Look", "link": "https://i.imgur.com/x.png"}, "social_blog", None) == ["R3"]
    assert llm_annotation.rule_flags(sources, {"tytuł": "Look", "link": "https://bbc.com/x"}, "media", None) == []
    wiki = llm_annotation.TASKS["sources_wikipedia"]
    assert llm_annotation.rule_flags(wiki, {"opis zmiany": "Anulowanie wersji 1 autorstwa X"}, "unknown", 0) == ["R9"]
    assert llm_annotation.rule_flags(wiki, {"opis zmiany": "akt., źródła/przypisy"}, "none", 0) == ["R10"]


def answers_frame(labels, confidence="high") -> pd.DataFrame:
    return pd.DataFrame({"unit_id": [f"u{index}" for index in range(len(labels))], "label": labels, "binary": None,
                         "confidence": confidence, "reason": "r"})


def test_combine_queues_disputes_rare_labels_and_a_control_share():
    task = llm_annotation.TASKS["stance"]
    labels = ["neutral"] * 200 + ["challenges", "supports"]
    first = answers_frame(labels)
    second = answers_frame(labels[:-1] + ["neutral"])
    records = pd.DataFrame({"unit_id": first["unit_id"]})
    queue = llm_annotation.combine(first, second, records, task, ["unit_id"], control_share=0.15, seed=1).set_index("unit_id")
    assert queue.loc["u200", "queue_reason"] == "rzadka etykieta" and queue.loc["u201", "queue_reason"] == "spór A1 i A2"
    assert queue.loc[["u200", "u201"], "p_review"].eq(1.0).all()
    accepted = queue.drop(index=["u200", "u201"])
    assert accepted["p_review"].eq(0.15).all()
    control = accepted["queue_reason"].eq("kontrola")
    assert 15 <= control.sum() <= 50 and accepted.loc[control, "decided_by"].eq("human").all()
    assert accepted.loc[~control, "decided_by"].eq("auto").all()
    low = llm_annotation.combine(answers_frame(["neutral"]), answers_frame(["neutral"], "low"), records.head(1), task, ["unit_id"])
    assert low.loc[0, "queue_reason"] == "niska pewność"


def test_auto_rows_count_without_verification():
    assert not annotation_sheets.unverified({"ai_source_types": "media", "verified": None, "decided_by": "auto"})
    assert annotation_sheets.unverified({"ai_source_types": "media", "verified": None, "decided_by": "human"})


def test_queue_sheet_round_trip_through_the_stance_reader(tmp_path):
    codebook = load_codebook()
    template = stance.workbook_path("gold", "A", tmp_path)
    stance.write_workbook(template, "A", "gold", posts(), codebook)
    task = llm_annotation.TASKS["stance"]
    first = pd.DataFrame({"unit_id": ["p1", "p2", "p3"], "label": ["challenges", "neutral", "not_applicable"], "binary": None,
                          "confidence": "high", "reason": "r"})
    queue = llm_annotation.combine(first, first, pd.DataFrame({"unit_id": ["p1", "p2", "p3"]}), task, ["unit_id"], control_share=0.0)
    output = tmp_path / "out" / "stance_gold_A.xlsx"
    llm_annotation.write_queue(template, output, stance.SHEET_NAME, queue, task, ["unit_id"], "test")
    labels, problems = stance.read_workbook(output, codebook, partial=True)
    # p1 (challenges) waits for a person; p2 and p3 were accepted automatically.
    assert labels["unit_id"].tolist() == ["p2", "p3"] and set(labels["decided_by"]) == {"auto"}
    assert labels["p_review"].eq(0.0).all()


def test_enriched_sample_strata_weights_and_splits():
    units = pd.DataFrame({"unit_id": [f"c{index}" for index in range(100)], "title": ["vaccines"] * 10 + ["study shows"] * 30 + ["hello"] * 60,
                          "text": "", "group": "conspiracy", "year": 2015})
    topics = pd.Series(["vaccines"] * 10 + ["none"] * 90)
    sample = stance.draw_enriched(units, topics, {"topic": None, "science_terms": 20, "rest": 10}, seed=3)
    by_stratum = sample.groupby("stratum").agg(n=("unit_id", "size"), inclusion=("inclusion", "first"))
    assert by_stratum.loc["topic", "n"] == 10 and by_stratum.loc["topic", "inclusion"] == 1.0
    assert by_stratum.loc["science_terms", "inclusion"] == pytest.approx(20 / 30)
    assert by_stratum.loc["rest", "inclusion"] == pytest.approx(10 / 60)
    assert sample.groupby("stratum")["split"].apply(lambda split: abs((split == "dev").sum() - (split == "test").sum()) <= 1).all()
    assert set(sample["annotator"]) == {"IS", "JP"} and sample["unit_id"].is_unique


def test_validation_frame_pools_sources_and_weights_reviewed_rows():
    manifest = pd.DataFrame({"unit_id": ["g1", "g2"], "platform": "reddit", "split": "test", "stratum": "s", "N_h": 100})
    gold_labels = pd.DataFrame({"unit_id": ["g1", "g2"], "platform": "reddit", "annotator": "A", "consensus_stance": ["neutral", "supports"],
                                "decided_by": ["auto", "human"], "p_review": [0.15, 1.0]})
    enriched_labels = pd.DataFrame({"unit_id": ["e1", "e2"], "platform": "reddit", "annotator": "B",
                                    "consensus_stance": ["challenges", "neutral"], "decided_by": ["human", "human"], "p_review": [1.0, 0.15]})
    sample = pd.DataFrame({"unit_id": ["e1", "e2"], "split": "test", "inclusion": [1.0, 0.5]})
    frame = stance.validation_frame(gold_labels, manifest, "test", enriched_labels, sample).set_index("unit_id")
    assert frame.groupby("source")["weight"].sum().to_dict() == {"enriched": pytest.approx(2.0), "gold": pytest.approx(2.0)}
    assert np.isnan(frame.loc["g1", "review_weight"]) and frame.loc["g2", "review_weight"] == pytest.approx(1.0)
    assert frame.loc["e2", "review_weight"] == pytest.approx(frame.loc["e2", "weight"] / 0.15)
