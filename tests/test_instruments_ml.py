"""Instrument input and the labelling steps of the model instruments, on fake model output (no downloads)."""

import pandas as pd

from digital_media_analysis.codebook import NO_SOURCE, load_codebook
from digital_media_analysis.instruments import gliner_v1, runner, zeroshot_v1
from digital_media_analysis.instruments.unit_text import reddit_text, unit_texts, wikipedia_text

SOURCE_CODES = set(load_codebook().category_codes) - {NO_SOURCE}


def units() -> pd.DataFrame:
    return pd.DataFrame([
        {"unit_id": "r1", "platform": "reddit", "group": "science", "title": "Study in mice", "text": "", "link": "https://www.nature.com/articles/x"},
        {"unit_id": "r2", "platform": "reddit", "group": "pics", "title": "My cat", "text": "", "link": "https://i.redd.it/abc.png"},
        {"unit_id": "COVID-19#5", "platform": "wikipedia", "group": "COVID-19", "text": "/* Objawy */ Przypis z EPWN"},
    ])


def test_reddit_text_keeps_the_link_but_not_own_media():
    assert reddit_text("Title", "Body", "https://bbc.co.uk/a") == "Title\nBody\nLink: https://bbc.co.uk/a"
    # Pictures the platform hosts for the author are never a source (R3).
    assert reddit_text("My cat", "", "https://i.redd.it/abc.png") == "My cat"


def test_wikipedia_text_drops_the_section_prefix():
    assert wikipedia_text("/* Przypisy */ źródła/przypisy") == "źródła/przypisy"
    assert wikipedia_text("/* Objawy */") == ""


def test_unit_texts_mix_platforms():
    texts = unit_texts(units())
    assert texts.to_dict() == {
        "r1": "Study in mice\nLink: https://www.nature.com/articles/x",
        "r2": "My cat",
        "COVID-19#5": "Przypis z EPWN",
    }


def test_hypotheses_cover_exactly_the_source_categories():
    for language in zeroshot_v1.LANGUAGES:
        assert set(zeroshot_v1.HYPOTHESES[language]) == SOURCE_CODES
        assert language in zeroshot_v1.EDIT_HYPOTHESES
    assert set(gliner_v1.ENTITY_LABELS.values()) <= SOURCE_CODES


def fake_scores() -> pd.DataFrame:
    rows = []
    for unit_id, platform, high in [("r1", "reddit", {"scientific": 0.9, "media": 0.6}), ("r2", "reddit", {}), ("COVID-19#5", "wikipedia", {"encyclopedia": 0.8, "edit_about_sources": 0.7})]:
        targets = [*SOURCE_CODES, *(["edit_about_sources"] if platform == "wikipedia" else [])]
        for language in zeroshot_v1.LANGUAGES:
            rows += [(unit_id, platform, language, target, high.get(target, 0.1) if language == "en" else 0.95) for target in targets]
    return pd.DataFrame(rows, columns=["unit_id", "platform", "language", "target", "score"])


def test_zeroshot_labels_apply_thresholds_language_and_none():
    labels = zeroshot_v1.labels(fake_scores(), {"reddit": "en", "wikipedia": "en"}, {"reddit": 0.5, "wikipedia": 0.5}, 0.5)
    assert labels[["unit_id", "cites_source", "source_types"]].values.tolist() == [
        ["r1", 1, "media;scientific"],
        ["r2", 0, "none"],
        ["COVID-19#5", 1, "encyclopedia"],
    ]
    assert labels["edit_about_sources"].tolist()[2] == 1 and pd.isna(labels["edit_about_sources"].tolist()[0])
    stricter = zeroshot_v1.labels(fake_scores(), {"reddit": "en", "wikipedia": "en"}, {"reddit": 0.7, "wikipedia": 0.9}, 0.9)
    assert stricter["source_types"].tolist() == ["scientific", "none", "none"]
    assert stricter["edit_about_sources"].tolist()[2] == 0
    # The other hypothesis language is a separate choice.
    polish = zeroshot_v1.labels(fake_scores(), {"reddit": "pl", "wikipedia": "pl"}, {"reddit": 0.5, "wikipedia": 0.5}, 0.5)
    assert polish["cites_source"].tolist() == [1, 1, 1]


def test_gliner_labels_keep_spans_above_threshold_and_type_bare_links_as_other():
    spans = pd.DataFrame([
        {"unit_id": "r1", "platform": "reddit", "label": "scientific journal or research paper", "category": "scientific", "span": "nature.com", "score": 0.8},
        {"unit_id": "r1", "platform": "reddit", "label": "news outlet or newspaper", "category": "media", "span": "Study", "score": 0.3},
        {"unit_id": "COVID-19#5", "platform": "wikipedia", "label": "encyclopedia or dictionary", "category": "encyclopedia", "span": "EPWN", "score": 0.6},
    ])
    labels = gliner_v1.labels(spans, units(), {"reddit": 0.5, "wikipedia": 0.5})
    assert labels["source_types"].tolist() == ["scientific", "none", "encyclopedia"]
    assert labels["edit_about_sources"].isna().all()
    # Without a kept span, the post link still cites an identified source: `other` (R7).
    strict = gliner_v1.labels(spans, units(), {"reddit": 0.9, "wikipedia": 0.9})
    assert strict["source_types"].tolist() == ["other", "none", "none"]


def test_rules_v1_adapter_reproduces_v1_document_labels():
    labels = runner.rules_v1_labels(pd.concat([
        units(),
        pd.DataFrame([{"unit_id": "COVID-19#6", "platform": "wikipedia", "group": "COVID-19", "text": "[[WP:SK]], drobne techniczne"}]),
    ], ignore_index=True))
    by_unit = labels.set_index("unit_id")
    # v1 reads only the post body, so the Reddit link posts cite nothing.
    assert by_unit.loc["r1", "source_types"] == "none" and by_unit.loc["r2", "source_types"] == "none"
    # v1's known error: a policy shortcut counts as an encyclopedic source.
    assert by_unit.loc["COVID-19#6", "source_types"] == "encyclopedia"
    assert labels["edit_about_sources"].isna().all()
    assert list(labels.columns) == runner.LABEL_COLUMNS
