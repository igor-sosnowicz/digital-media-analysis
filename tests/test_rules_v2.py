import pandas as pd
import pytest

from digital_media_analysis.instruments import refs_v1, rules_v2


@pytest.mark.parametrize(("comment", "codes", "edit"), [
    # R10: the edit-type tag alone is work on references, not a citation.
    ("akt., źródła/przypisy", set(), 1),
    # R9: the section prefix does not count, shortcuts and reverts are technical.
    ("/* Przypisy */ drobne redakcyjne", set(), 0),
    ("[[WP:SK]], drobne techniczne", set(), 0),
    ("Wycofano edycje użytkownika [[Special:Contributions/1.2.3.4|1.2.3.4]]", set(), 0),
    ("[[WP:MARTWE|poprawa martwych linków zewnętrznych]]", set(), 1),
    # A named source after a cue decides the category; a cue without one is unknown (R5).
    ("Przypis z EPWN", {"encyclopedia"}, 1),
    ("aktualizacja i rozbudowa w oparciu o IPCC AR6 WGI", {"institutional"}, 0),
    ("wg źródła jeszcze kapusta", {"unknown"}, 1),
    ("ta zakładka nawet podaje ECDC https://www.ecdc.europa.eu/en", {"institutional"}, 0),
    # R8: own opinion is no citation; "za" is no cue.
    ("wg mnie to bzdura", set(), 0),
    ("za dużo tekstu", set(), 0),
])
def test_wikipedia_rules_follow_the_codebook(comment, codes, edit):
    assert rules_v2.wikipedia_labels(comment) == (codes, edit)


@pytest.mark.parametrize(("title", "body", "link", "codes"), [
    ("Cats", "", "https://www.youtube.com/watch?v=1", {"social_blog"}),
    ("Cats", "", "https://www.cnn.com/a", {"media"}),
    ("Cats", "", "https://bps-research-digest.blogspot.com/a", {"social_blog"}),
    ("Cats", "", "https://www.unknown-site.com/a", {"other"}),
    # R3: own pictures, survey forms and user profiles are not sources.
    ("My cat", "", "https://i.imgur.com/x.jpg", set()),
    ("Survey", "", "https://docs.google.com/forms/d/1", set()),
    ("Look", "", "https://www.reddit.com/user/someone", set()),
    # Whole words only: no "gus" in "Ferguson".
    ("Ferguson unrest", "", "", set()),
    ("Study shows cats sleep a lot", "", "", {"scientific"}),
    ("According to the CDC, flu is up", "", "", {"institutional"}),
    ("In my opinion this is fine", "", "", set()),
    ("Doctors", "As a nurse I see this every day.", "", {"personal"}),
])
def test_reddit_rules_read_link_and_text(title, body, link, codes):
    assert rules_v2.reddit_labels(title, body, link) == codes


def test_document_labels_prefer_concrete_sources():
    units = pd.DataFrame({
        "unit_id": ["r1", "r2", "COVID-19#3"], "platform": ["reddit", "reddit", "wikipedia"],
        "title": ["According to the BBC and sources", "Hi", ""], "text": ["", "", "źródła/przypisy"],
        "link": ["", "", ""],
    })
    labels = rules_v2.labels(units)
    assert labels[["cites_source", "source_types"]].values.tolist() == [[1, "media"], [0, "none"], [0, "none"]]
    assert labels["edit_about_sources"].tolist()[2] == 1 and pd.isna(labels["edit_about_sources"].iloc[0])


def test_references_count_ref_bodies_and_templates_outside_them():
    text = 'A<ref name="a">{{Cytuj stronę|url=x}}</ref> B<ref name="a" /> {{cytuj książkę | tytuł = T}} <ref>Y</ref>'
    found = refs_v1.references(text)
    assert sum(found.values()) == 3


def test_reference_changes_compare_each_revision_with_the_previous_one():
    revisions = [
        ("P", 1, "x<ref>A</ref>"),
        ("P", 2, "x<ref>A</ref><ref>B</ref>"),
        # Moving a reference changes nothing; editing one removes the old body and adds the new one.
        ("P", 3, "<ref>B</ref> x <ref>A</ref>"),
        ("P", 4, "<ref>B2</ref> x <ref>A</ref>"),
        ("Q", 1, "<ref>C</ref>"),
    ]
    table = refs_v1.changes(revisions)
    assert table[["revision_number", "added", "removed"]].values.tolist() == [[1, 1, 0], [2, 1, 0], [3, 0, 0], [4, 1, 1], [1, 1, 0]]
    only = refs_v1.changes(revisions, wanted={("P", 3)})
    assert only[["refs_before", "refs_after"]].values.tolist() == [[2, 2]]
    raw = table.assign(unit_id=table["page"] + "#" + table["revision_number"].astype(str), platform="wikipedia")
    labels = refs_v1.labels(raw, threshold=2)
    assert labels["edit_about_sources"].tolist() == [0, 0, 0, 1, 0]
    assert labels["cites_source"].isna().all() and labels["source_types"].isna().all()
