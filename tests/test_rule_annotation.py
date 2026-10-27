import pandas as pd

from digital_media_analysis import llm_annotation, rule_annotation, stance
from digital_media_analysis.codebook import load_codebook
from test_stance import posts


def test_stance_rule_rules_out_only_non_science_subreddits_without_science_words():
    label = rule_annotation.rule_label
    assert label("stance", {"subreddit": "conspiracy", "tytuł": "The Fed is printing money", "link": ""})[0] == "not_applicable"
    assert label("stance", {"subreddit": "conspiracy", "tytuł": "Vaccines cause autism", "link": ""})[0] is None
    assert label("stance", {"subreddit": "science", "tytuł": "Water found on Mars", "link": ""})[0] is None


def test_source_rules():
    label = rule_annotation.rule_label
    assert label("sources_reddit", {"tytuł": "My cat", "treść": "", "link": "https://i.imgur.com/x.png"})[0] == "none"
    assert label("sources_reddit", {"tytuł": "My cat, according to my vet", "treść": "", "link": "https://i.imgur.com/x.png"})[0] is None
    assert label("sources_reddit", {"tytuł": "What do you think?", "treść": "", "link": ""})[0] == "none"
    assert label("sources_reddit", {"tytuł": "Read this", "treść": "", "link": "https://bbc.com/x"})[0] is None
    assert label("sources_wikipedia", {"opis zmiany": "Anulowanie wersji 1 autorstwa X"})[:2] == ("none", 0)
    assert label("sources_wikipedia", {"opis zmiany": "Anulowanie wersji 1 autorstwa X – brak źródła"})[0] is None
    assert label("sources_wikipedia", {"opis zmiany": "/* Objawy */ drobne redakcyjne, źródła/przypisy"})[:2] == ("none", 1)
    assert label("sources_wikipedia", {"opis zmiany": "według WHO"})[0] is None


def test_error_cause_and_domain_rules():
    label = rule_annotation.rule_label
    url = {"instrument": "rules_v1", "variable": "cites_source", "error": "FN", "platform": "reddit", "tekst": "x", "link": "https://a.com"}
    assert label("error_cause", url)[0] == "pominięte pole url"
    shortcut = {"instrument": "rules_v1", "variable": "cites_source", "error": "FP", "platform": "wikipedia",
                "tekst": "[[WP:SK]], drobne redakcyjne", "link": ""}
    assert label("error_cause", shortcut)[0] == "skrót WP:"
    assert label("domain", {"domain": "a.pl", "category": "media", "links": "2"})[0] == "media"
    assert label("domain", {"domain": "b.pl", "category": "social_blog", "links": "1"})[0] is None
    assert label("domain", {"domain": "c.pl", "category": "media", "links": "12"})[0] is None


def test_queue_is_blind_for_people_and_keeps_rule_labels_for_control(tmp_path):
    records = pd.DataFrame({"unit_id": [f"u{index}" for index in range(300)], "subreddit": "conspiracy",
                            "tytuł": ["The Fed again"] * 200 + ["Vaccines are poison"] * 100, "treść": "", "link": ""})
    queue = rule_annotation.queue(records, "stance", ["unit_id"], control_share=0.15, seed=2).set_index("unit_id")
    ruled = queue.iloc[:200]
    assert ruled["suggestion"].eq("not_applicable").all() and ruled["p_review"].eq(0.15).all()
    control = ruled["queue_reason"].eq("kontrola reguły")
    assert 15 <= control.sum() <= 50 and ruled.loc[control, "decided_by"].eq("human").all()
    assert queue.iloc[200:]["decided_by"].eq("human").all() and queue.iloc[200:]["p_review"].eq(1.0).all()
    view = rule_annotation.sheet_view(queue.reset_index())
    human = view["decided_by"].eq("human")
    assert view.loc[human, "suggestion"].isna().all() and view.loc[human, "queue_reason"].eq(rule_annotation.HUMAN_REASON).all()


def test_rule_queue_sheet_round_trip(tmp_path):
    codebook = load_codebook()
    template = stance.workbook_path("gold", "A", tmp_path)
    units = posts().assign(group="conspiracy", title=["Vaccines cause autism, wake up", "New study on bees", "My cat"])
    stance.write_workbook(template, "A", "gold", units, codebook)
    records = llm_annotation.read_rows(template, stance.SHEET_NAME)
    queue = rule_annotation.queue(records, "stance", ["unit_id"], control_share=0.0)
    output = tmp_path / "review" / "stance_gold_A.xlsx"
    llm_annotation.write_queue(template, output, stance.SHEET_NAME, rule_annotation.sheet_view(queue),
                               llm_annotation.TASKS["stance"], ["unit_id"], "test")
    labels, problems = stance.read_workbook(output, codebook, partial=True)
    # Only "My cat" is decided by the rule; the other two wait for a person, without a label shown.
    assert labels["unit_id"].tolist() == ["p3"] and labels["consensus_stance"].tolist() == ["not_applicable"]
    assert labels["decided_by"].tolist() == ["auto"]
    rows = llm_annotation.read_rows(output, stance.SHEET_NAME).set_index("unit_id")
    assert rows.loc[["p1", "p2"], "consensus_stance"].isna().all()


def test_ai_suggestions_fill_only_rows_for_a_person(tmp_path):
    from digital_media_analysis import ai_suggestions

    codebook = load_codebook()
    template = stance.workbook_path("gold", "A", tmp_path)
    units = posts().assign(group="conspiracy", title=["Vaccines cause autism, wake up", "New study on bees", "My cat"])
    stance.write_workbook(template, "A", "gold", units, codebook)
    queue = rule_annotation.queue(llm_annotation.read_rows(template, stance.SHEET_NAME), "stance", ["unit_id"], control_share=0.0)
    output = tmp_path / "review" / "stance_gold_A.xlsx"
    llm_annotation.write_queue(template, output, stance.SHEET_NAME, rule_annotation.sheet_view(queue),
                               llm_annotation.TASKS["stance"], ["unit_id"], "test")
    suggestions = pd.DataFrame({"unit_id": ["p1", "p2", "p3"], "ai_consensus_stance": ["challenges", "neutral", "supports"],
                                "ai_uncertain": [0, 1, 0], "ai_reason": ["a", "b", "c"]})
    assert ai_suggestions.fill_queue_rows(output, stance.SHEET_NAME, ["unit_id"], suggestions, "consensus_stance") == 2
    rows = llm_annotation.read_rows(output, stance.SHEET_NAME).set_index("unit_id")
    assert rows.loc["p1", "consensus_stance"] == "challenges" and rows.loc["p3", "consensus_stance"] == "not_applicable"
    labels, _ = stance.read_workbook(output, codebook, partial=True)
    # The suggested rows wait for verified = 1; the rule row counts.
    assert labels["unit_id"].tolist() == ["p3"]
