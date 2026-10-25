import pandas as pd
import pytest

from digital_media_analysis import wikipedia_refs
from digital_media_analysis.codebook import load_codebook

ARTICLE = (
    "Tekst.<ref>{{Cytuj |url=https://www.who.int/news/item/1 |tytuł=WHO}}</ref> "
    "Dalej.<ref name=\"a\">https://web.archive.org/web/2020/https://tvn24.pl/x.html.</ref> "
    "Bez przypisu https://youtube.com/watch?v=1"
)


def test_reference_links_read_only_references_and_unwrap_archives():
    links = wikipedia_refs.reference_links(ARTICLE)
    assert links == {"https://www.who.int/news/item/1": 1, "https://tvn24.pl/x.html": 1}
    assert wikipedia_refs.domain("https://www.who.int/news/item/1") == "who.int"


def test_added_links_are_a_multiset_difference_per_page():
    revisions = [
        ("A", 1, "2020-01-01T00:00:00Z", "<ref>https://a.org/1</ref>"),
        ("A", 2, "2020-02-01T00:00:00Z", "x<ref>https://a.org/1</ref> moved"),
        ("A", 3, "2021-01-01T00:00:00Z", "<ref>https://a.org/1</ref><ref>https://a.org/1</ref><ref>https://b.pl/2</ref>"),
        ("B", 1, "2021-03-01T00:00:00Z", "<ref>https://a.org/1</ref>"),
    ]
    added = wikipedia_refs.added_links(revisions)
    assert added[["page", "revision_number", "domain"]].values.tolist() == [
        ["A", 1, "a.org"], ["A", 3, "a.org"], ["A", 3, "b.pl"], ["B", 1, "a.org"],
    ]


def test_categorise_takes_the_longest_matching_suffix():
    mapping = {"nih.gov": "institutional", "ncbi.nlm.nih.gov": "scientific", "gov.pl": "other",
               "pzh.gov.pl": "institutional", "edu.pl": "institutional", "prep.edu.pl": "other"}
    domains = pd.Series(["ncbi.nlm.nih.gov", "fda.nih.gov", "szczepienia.pzh.gov.pl", "mz.gov.pl", "prep.edu.pl", "uw.edu.pl", "blog.example.com", "xgov.pl"])
    assert wikipedia_refs.categorise(domains, mapping).tolist() == [
        "scientific", "institutional", "institutional", "other", "other", "institutional", "unclassified", "unclassified",
    ]


def test_domain_list_uses_codebook_categories_and_lists_each_domain_once():
    mapping = wikipedia_refs.load_domain_categories()
    assert set(mapping.values()) <= set(load_codebook().category_codes) | {wikipedia_refs.UNCLASSIFIED}
    assert mapping["pscp.tv"] == "social_blog" and mapping["github.com"] == "other"


def test_duplicate_domain_is_rejected(tmp_path):
    path = tmp_path / "domains.yaml"
    path.write_text("version: '1'\nmedia: [a.pl]\nother: [a.pl]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="a.pl"):
        wikipedia_refs.load_domain_categories(path)
