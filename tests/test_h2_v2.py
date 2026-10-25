import pandas as pd
import pytest

from digital_media_analysis import owners, rsp, wikipedia_frame, wikipedia_history


def fake_categories(params):
    tree = {
        "Kategoria:Medycyna": [{"ns": 0, "pageid": 1, "title": "Lekarz"}, {"ns": 14, "pageid": 90, "title": "Kategoria:Choroby"}],
        "Kategoria:Choroby": [{"ns": 0, "pageid": 2, "title": "Grypa"}, {"ns": 0, "pageid": 1, "title": "Lekarz"},
                              {"ns": 14, "pageid": 91, "title": "Kategoria:Rzadkie"}],
        "Kategoria:Rzadkie": [{"ns": 0, "pageid": 3, "title": "Choroba X"}],
        "Kategoria:Matematyka": [{"ns": 0, "pageid": 4, "title": "Liczba"}, {"ns": 0, "pageid": 2, "title": "Grypa"}],
    }
    members = tree.get(params["cmtitle"], [])
    if "cmcontinue" in params:
        return {"query": {"categorymembers": members[1:]}}
    return {"query": {"categorymembers": members[:1]}, "continue": {"cmcontinue": "next"}} if len(members) > 1 else {"query": {"categorymembers": members}}


def test_category_members_follow_subcategories_to_the_depth_and_continuation():
    members = wikipedia_frame.category_members(fake_categories, "Medycyna", depth=1)
    assert members["title"].tolist() == ["Lekarz", "Grypa"]
    assert members.set_index("title").loc["Grypa", "path"] == "Medycyna > Choroby"
    deeper = wikipedia_frame.category_members(fake_categories, "Medycyna", depth=2)
    assert "Choroba X" in set(deeper["title"])


def test_build_frame_counts_a_page_once_in_the_first_group():
    frame, sizes = wikipedia_frame.build_frame(fake_categories, {"health": ["Medycyna"], "control": ["Matematyka"]}, 2, 10, seed=1)
    assert frame.groupby("group")["title"].apply(sorted).to_dict() == {"control": ["Liczba"], "health": ["Choroba X", "Grypa", "Lekarz"]}
    assert sizes["control"]["pages"] == 1


def revision(revid, timestamp, links, sha1, tags=()):
    return {"pageid": 7, "ns": 0, "title": "Grypa", "revid": revid, "timestamp": timestamp, "user": "u", "anon": False,
            "sha1": sha1, "tags": list(tags), "links": links}


def test_reverts_by_identity_and_by_tag():
    revisions = [revision(1, "2020-01-01", {}, "a"), revision(2, "2020-01-02", {}, "b"), revision(3, "2020-01-03", {}, "c"),
                 revision(4, "2020-01-04", {}, "a"), revision(5, "2020-01-05", {}, "d", ["mw-reverted"])]
    assert wikipedia_history.mark_reverts(revisions) == [False, True, True, False, True]


def test_link_events_mark_first_additions_reverted_edits_and_survival():
    revisions = [
        revision(1, "2019-12-31T00:00:00Z", {"https://old.org/x": 1}, "s0"),
        revision(2, "2020-01-01T00:00:00Z", {"https://old.org/x": 1, "https://blog.example.com/a": 1}, "s1"),
        revision(3, "2020-01-11T00:00:00Z", {"https://old.org/x": 1}, "s0"),
        revision(4, "2020-02-01T00:00:00Z", {"https://old.org/x": 1, "https://blog.example.com/a": 1}, "s1b"),
    ]
    events = wikipedia_history.link_events(revisions, "2020-03-02T00:00:00Z")
    assert events["url"].tolist() == ["https://blog.example.com/a"] * 2
    assert events["first_addition"].tolist() == [True, False]
    # Revision 2 was undone by revision 3, which restored the text of revision 1.
    assert events["reverted_edit"].tolist() == [True, False]
    assert events["days_present"].round(1).tolist() == [10.0, 30.0] and events["censored"].tolist() == [False, True]


def test_revision_record_keeps_reference_links_or_all_links_on_talk_pages():
    content = 'Tekst <ref>{{Cytuj|url=https://who.int/a}}</ref> i https://blog.example.com/b'
    api = {"revid": 5, "timestamp": "2021-01-01T00:00:00Z", "sha1": "x", "slots": {"main": {"content": content}}}
    article = wikipedia_history.revision_record({"pageid": 1, "ns": 0, "title": "A"}, api)
    talk = wikipedia_history.revision_record({"pageid": 2, "ns": 1, "title": "Dyskusja:A"}, api)
    assert list(article["links"]) == ["https://who.int/a"] and article["refs"] == 1
    assert set(talk["links"]) == {"https://who.int/a", "https://blog.example.com/b"}


def test_fetch_history_keeps_the_starting_revision_and_continues():
    def get(params):
        page = {"pageid": 1, "ns": 0, "title": "A"}
        rev = lambda revid, ts: {"revid": revid, "timestamp": ts, "sha1": str(revid), "slots": {"main": {"content": ""}}}  # noqa: E731
        if params.get("rvdir") == "older":
            return {"query": {"pages": [{**page, "revisions": [rev(1, "2014-12-01T00:00:00Z")]}]}}
        if "rvcontinue" not in params:
            return {"query": {"pages": [{**page, "revisions": [rev(2, "2015-02-01T00:00:00Z")]}]}, "continue": {"rvcontinue": "x"}}
        return {"query": {"pages": [{**page, "revisions": [rev(3, "2016-01-01T00:00:00Z"), rev(4, "2030-01-01T00:00:00Z")]}]}}

    records = list(wikipedia_history.fetch_history(get, "A", "2015-01-01T00:00:00Z", "2027-01-01T00:00:00Z"))
    assert [record["revid"] for record in records] == [1, 2, 3]


@pytest.mark.parametrize(("url", "expected"), [
    ("https://twitter.com/GIS_gov/status/123", ("twitter.com", "gis_gov")),
    ("https://x.com/someone", ("twitter.com", "someone")),
    ("https://www.pscp.tv/WHO/1abc", ("pscp.tv", "who")),
    ("https://www.youtube.com/watch?v=abc123", ("youtube.com", "video:abc123")),
    ("https://youtu.be/abc123", ("youtube.com", "video:abc123")),
    ("https://www.youtube.com/@DrJohn/videos", ("youtube.com", "@drjohn")),
    ("https://www.youtube.com/channel/UC123", ("youtube.com", "channel/uc123")),
    ("https://monbiot.blogspot.com/2020/01/x.html", ("blogspot.com", "monbiot")),
    ("https://medium.com/@writer/post", ("medium.com", "writer")),
    ("https://www.facebook.com/sharer.php?u=x", None),
    ("https://www.who.int/news", None),
])
def test_account_of(url, expected):
    assert owners.account_of(url) == expected


def test_owner_types_come_from_the_codebook_list():
    types, accounts = owners.load_owner_types()
    assert accounts["pscp.tv/who"] == "institution" and "independent_expert" in types
    table = owners.classify(pd.Series(["https://www.pscp.tv/WHO/1", "https://youtu.be/zz", "https://who.int/a"]), accounts)
    assert table["owner_type"].tolist() == ["institution", owners.UNCODED, ""]
    links = pd.concat([table, pd.DataFrame({"url": ["https://www.pscp.tv/WHO/1", "https://youtu.be/zz", "https://who.int/a"],
                                            "pageid": [1, 2, 3], "timestamp": ["2020", "2021", "2022"]})], axis=1)
    review = owners.review_table(links)
    assert review["key"].tolist() == ["pscp.tv/who", "youtube.com/video:zz"]


def test_rsp_parse_reads_status_and_domains():
    wikitext = (
        "{|\n|-\n| [[Daily Mail]] || {{/Status|d}} || ... || {{/Uses|dailymail.co.uk|thisismoney.co.uk}}\n"
        "|-\n| [[Reuters]] || {{WP:RSPSTATUS|gr}} || {{WP:RSPUSES|reuters.com}}\n"
        "|-\n| [[Blog]] || {{/Status|gr}} {{/Status|gu}} || {{/Uses|example.blog}}\n|}"
    )
    table = rsp.parse(wikitext).set_index("domain")["status"].to_dict()
    assert table == {"dailymail.co.uk": "d", "thisismoney.co.uk": "d", "reuters.com": "gr", "example.blog": "gu"}
    assert rsp.status_of(pd.Series(["www.dailymail.co.uk".removeprefix("www."), "news.reuters.com", "x.org"]), table).tolist() == ["d", "gr", ""]
