"""Pin the behaviour of the frozen v1 instrument, including its known errors.

If one of these tests fails, v1 was changed. Revert it and put the fix in a new
instrument version instead, so validation keeps a stable baseline.
"""

import pandas as pd

from digital_media_analysis.instruments import rules_v1
from digital_media_analysis.instruments.labels import to_document_labels


def categories(mentions: list[dict]) -> set[tuple[str, str]]:
    return {(mention["reference"], mention["category"]) for mention in mentions}


def test_reddit_url_counts_as_link_and_keyword_category():
    mentions = rules_v1.extract_reddit_mentions("https://wiadomosci.wp.pl/artykul")
    assert categories(mentions) == {
        ("wiadomosci.wp.pl", "link/domena"),
        ("wp.pl", "media informacyjne"),
    }


def test_reddit_substring_matches_inside_words():
    mentions = rules_v1.extract_reddit_mentions("Pamiętam, że była związana z bogusiem.")
    assert ("gus", "źródła oficjalne") in categories(mentions)


def test_reddit_keyword_without_source_function_is_matched():
    mentions = rules_v1.extract_reddit_mentions("Zbieramy/szukamy znajomych do wyjść.")
    assert categories(mentions) == {("znajomy", "źródła osobiste i społecznościowe")}


def test_reddit_cue_only_when_nothing_else_found():
    assert categories(rules_v1.extract_reddit_mentions("Czytałem o tym wczoraj.")) == {
        ("niesprecyzowane źródło", "sygnał powołania"),
    }
    assert rules_v1.extract_reddit_mentions("Zwykły post bez odniesień.") == []


def test_reddit_references_ignore_url_column():
    df = pd.DataFrame({
        "subreddit": ["PolskaPolityka"],
        "score": [1],
        "num_comments": [0],
        "title": ["Tytuł"],
        "text": [""],
        "url": ["https://wiadomosci.wp.pl/artykul"],
    })
    assert rules_v1.extract_reddit_references(df).empty


def wikipedia_frame(*comments: str) -> pd.DataFrame:
    return pd.DataFrame({
        "page": "COVID-19",
        "revision_number": range(1, len(comments) + 1),
        "comment": comments,
    })


def test_wikipedia_policy_shortcut_is_an_encyclopedic_source():
    references = rules_v1.extract_wikipedia_references(wikipedia_frame("[[WP:SK]], drobne techniczne"))
    assert references[["reference", "source_category", "confidence"]].values.tolist() == [
        ["WP:SK", "źródła encyklopedyczne", 0.90],
    ]


def test_wikipedia_footnote_tag_is_an_unspecified_citation():
    references = rules_v1.extract_wikipedia_references(wikipedia_frame("drobne redakcyjne, źródła/przypisy"))
    assert references[["source_category", "confidence", "cue"]].values.tolist() == [
        ["powołanie bez wskazanego źródła", 0.55, "źródła"],
    ]


def test_wikipedia_category_leaks_from_rest_of_comment():
    references = rules_v1.extract_wikipedia_references(
        wikipedia_frame("[[WP:POP]] według instytutu")
    )
    assert references["source_category"].tolist() == ["nauka i edukacja"]


def test_wikipedia_url_domain_is_classified():
    references = rules_v1.extract_wikipedia_references(
        wikipedia_frame("objawy według WHO (https://www.who.int/q-a)")
    )
    assert references[["domain", "source_category"]].values.tolist() == [
        ["who.int", "instytucje publiczne"],
    ]


def test_document_labels_map_v1_into_codebook_space():
    units = wikipedia_frame("[[WP:SK]]", "bez odniesień", "drobne redakcyjne, źródła/przypisy")
    references = rules_v1.extract_wikipedia_references(units)
    labels = to_document_labels(
        references,
        units,
        unit_columns=["page", "revision_number"],
        category_column="source_category",
        category_map=rules_v1.WIKIPEDIA_CATEGORY_MAP,
        non_citation=rules_v1.WIKIPEDIA_NON_CITATION,
    )
    assert labels[["revision_number", "cites_source", "source_types"]].values.tolist() == [
        [1, 1, "encyclopedia"],
        [2, 0, "none"],
        [3, 1, "unknown"],
    ]


def test_document_labels_link_without_type_is_other():
    units = pd.DataFrame({"row_index": [0, 1]})
    mentions = pd.DataFrame({"row_index": [0, 1, 1], "category": ["link/domena", "link/domena", "media informacyjne"]})
    labels = to_document_labels(
        mentions, units, ["row_index"], "category", rules_v1.REDDIT_CATEGORY_MAP,
    )
    # An untyped link alone is an identified source of no other category; next to a typed one it adds nothing.
    assert labels[["cites_source", "source_types"]].values.tolist() == [[1, "other"], [1, "media"]]
