"""Instrument I2 (rules_v2): source rules written from the codebook, built on the dev split only.

It fixes the failures of v1 listed in docs/plan_walidacji.md (diagnosis):
- whole words only, so "gus" in "Ferguson" no longer matches (#3);
- Reddit: the unit as the codebook defines it, title, body and the post link
  (#4); the author's own pictures (left out of the unit text), survey forms and
  user profiles are not sources (R3);
- the domain of a link decides its category (R4): `codebook/domains.yaml`, then
  `REDDIT_DOMAINS`, then host patterns for blogs and news sites; an unknown
  domain is `other` (R7);
- Wikipedia: the section prefix, policy and tool shortcuts (`[[WP:…]]`,
  `[[Pomoc:…]]`), links to users and reverts are technical, not sources (R9, #5);
- Wikipedia: the "źródła/przypisy" tag and other work on references set
  `edit_about_sources` only (R10, #6);
- a category comes from the mention itself, a link or a name right after a
  citation cue ("according to", "wg", "na podstawie", "przypis z"), never from
  other words of the text (#5); a cue without a recognisable source is
  `unknown` (R5); own opinion and requests for sources are not citations (R8).
"""

import re
from functools import cache

import pandas as pd

from digital_media_analysis.codebook import NO_SOURCE
from digital_media_analysis.instruments.labels import LABEL_SEPARATOR
from digital_media_analysis.instruments.unit_text import OWN_MEDIA_HOSTS, link_host, wikipedia_text
from digital_media_analysis.wikipedia_refs import UNCLASSIFIED, categorise, load_domain_categories

VERSION = "v2"
LABEL_COLUMNS = ["unit_id", "platform", "cites_source", "source_types", "edit_about_sources"]
UNTYPED = "other"

# Frequent Reddit link domains missing from codebook/domains.yaml (built for Wikipedia references).
REDDIT_DOMAINS = {
    "scientific": ["plosone.org", "jneurosci.org", "physiology.org", "aps.org", "acs.org", "rsc.org", "ssrn.com", "researchgate.net"],
    "institutional": ["eurekalert.org", "alphagalileo.org", "esa.int", "cern.ch", "un.org", "worldbank.org", "oecd.org",
                      "europa.eu", "census.gov", "bls.gov", "nsf.gov", "usgs.gov", "epa.gov"],
    "media": ["phys.org", "physorg.com", "medicalxpress.com", "newscientist.com", "livescience.com", "scientificamerican.com",
              "sciam.com", "wired.com", "npr.org", "nbcnews.com", "msnbc.com", "cbsnews.com", "abcnews.go.com", "cnn.com",
              "foxnews.com", "usatoday.com", "latimes.com", "chicagotribune.com", "theguardian.com", "guardian.co.uk",
              "telegraph.co.uk", "independent.co.uk", "huffingtonpost.com", "huffpost.com", "slate.com", "salon.com",
              "theatlantic.com", "newsweek.com", "rawstory.com", "alternet.org", "motherjones.com", "politico.com",
              "thehill.com", "apnews.com", "ap.org", "news.yahoo.com", "news.discovery.com", "nationalgeographic.com",
              "smithsonianmag.com", "arstechnica.com", "rt.com", "infowars.com", "breitbart.com", "theintercept.com",
              "oko.press", "rp.pl", "tvp.pl", "polsatnews.pl", "radiozet.pl", "rmf24.pl", "natemat.pl", "spidersweb.pl",
              "money.pl", "bankier.pl", "wp.pl", "o2.pl", "fakt.pl", "se.pl", "niezalezna.pl", "dorzeczy.pl"],
    "social_blog": ["youtu.be", "vimeo.com", "dailymotion.com", "liveleak.com", "metacafe.com", "medium.com", "substack.com",
                    "wordpress.com", "blogspot.com", "blogs.com", "tumblr.com", "steemit.com", "facebook.com", "fb.com",
                    "instagram.com", "tiktok.com", "x.com", "t.co", "twitch.tv", "rumble.com", "bitchute.com", "wykop.pl",
                    "soundcloud.com", "podcasts.apple.com", "zerohedge.com"],
    "encyclopedia": ["wikipedia.org", "britannica.com", "wiktionary.org", "merriam-webster.com", "dictionary.com", "pwn.pl"],
}
# Hosts that are never a source (R3): survey forms and user profiles.
FORM_HOSTS = {"forms.gle", "surveymonkey.com", "typeform.com", "strawpoll.me", "goo.gl"}
BLOG_HOST = re.compile(r"(^|[.-])blogs?([.-]|$)")
NEWS_HOST = re.compile(r"(^|[.-])(news|times|post|tribune|herald|gazette|daily|press|tv|radio|wiadomosci)([.-]|$)")
URL = re.compile(r"https?://[^\s<>\"'\]\)|]+", re.IGNORECASE)

# Named sources, matched as whole words right after a citation cue; acronyms are case-sensitive.
NAMES = {
    "scientific": r"doi|pubmed|arxiv|PNAS|NEJM|BMJ|JAMA|the lancet|lancet|journal of \w+|peer[- ]reviewed|meta-?analys\w+|"
                  r"metaanaliz\w+|czasopism\w+ naukow\w+|publikacj\w+ naukow\w+|artykuł\w* naukow\w+|bada\w+ naukow\w+|"
                  r"badani\w+|study|studies|research(?:ers)?|naukowc\w+|uniwersytet\w*|university",
    "institutional": r"WHO|CDC|ECDC|NIH|NASA|NOAA|IPCC|EMA|FDA|GUS|Eurostat|PZH|NIZP|WMO|Światow\w+ Organizacj\w+ Zdrowia|"
                     r"World Health Organi[sz]ation|Główn\w+ Urząd Statystyczny|Narodow\w+ Instytut\w* Zdrowia",
    "media": r"BBC|CNN|Reuters|Associated Press|AP|New York Times|NYT|Guardian|Washington Post|Fox News|TVN\w*|TVP\w*|Polsat\w*|"
             r"Onet\w*|Gazet\w+ Wyborcz\w+|Rzeczpospolit\w+|Interi\w+|PAP|gazet\w+|dziennik\w*|tygodnik\w*|portal\w*|newspaper|"
             r"news(?:paper)? article|article in",
    "social_blog": r"YouTube|Twitter\w*|tweet\w*|tweecie|Facebook\w*|Instagram\w*|TikTok\w*|blog\w*|podcast\w*|influencer\w*|vlog\w*",
    "encyclopedia": r"Wikipedi\w+|Britannic\w+|EPWN|PWN|encyklopedi\w+|encyclop(?:a)?edi\w+|słownik\w*|dictionary",
}
REDDIT_CUE = re.compile(
    r"\b(?:according to|source[sd]?\s*:|sources?\s+say|via|reported by|published in|as reported|"
    r"study (?:shows|finds|found|suggests)|studies (?:show|find|suggest)|researchers (?:say|found|show)|"
    r"według|wg\.?|źródło\s*:|źródła\s*:|jak podaje|donosi|podaje)\s*",
    re.IGNORECASE,
)
WIKIPEDIA_CUE = re.compile(
    r"(?:\bwg\.?|\bw/g|\bwedług|\bna podstawie|\bw oparciu o|\bzgodnie z|\bźródło\s*:|\bźródła\s*:|\bprzypis(?:y)? z"
    r")\s*",
    re.IGNORECASE,
)
GENERIC_SOURCE = re.compile(r"\bźród\w+|\bsource\w*\b|\bdan\w+\b|\bdata\b|\braport\w*|\breport\w*", re.IGNORECASE)
WINDOW = 60
# Own experience is a source by itself (category personal), without a cue.
PERSONAL = re.compile(
    r"\b(?:in my experience|from (?:my own|personal) experience|i (?:work|worked) (?:as|at|in)|as an? (?:doctor|nurse|physician|"
    r"scientist|engineer|teacher|researcher|pharmacist|biologist|chemist|physicist)|my (?:doctor|friend|wife|husband|mom|dad|"
    r"brother|sister) (?:told|said|works)|z własnego doświadczenia|z doświadczenia|u mnie w pracy|pracuję jako|"
    r"mój znajomy (?:lekarz|pracuje)|moja znajoma (?:lekarka|pracuje))\b",
    re.IGNORECASE,
)
# Not a citation (R8): own opinion and requests for sources.
OPINION = re.compile(r"\b(?:według mnie|wg mnie|moim zdaniem|in my opinion|imo|imho)\b", re.IGNORECASE)

# Wikipedia technical elements (R9).
TECHNICAL_LINK = re.compile(
    r"\[\[(?:WP|WPT|WT|Pomoc|Help|Special|Specjalna|Wikipedysta|Wikipedystka|User|User talk|Dyskusja wikipedysty|"
    r"Dyskusja wikipedystki|Wikipedia|Kategoria|Category|Plik|File|Image|Grafika|Szablon|Template)\s*:[^\]]*\]\]",
    re.IGNORECASE,
)
REVERT = re.compile(r"^\s*(?:Wycofano edycj|Anulowanie wersji|Przywrócono|Cofnięto|Reverted|Undid|Wycofanie)", re.IGNORECASE)
WIKI_HOSTS = ("wikipedia.org", "wikimedia.org", "wikidata.org", "wikiwand.com", "toolforge.org", "wmflabs.org")
# Work on references (R10): the edit-type tag, references, sources, bibliography and dead links, also as shortcuts.
EDIT_CUE = re.compile(
    r"źródła/przypisy|\bprzypis\w*|\bźród\w+|\bbibliografi\w*|\bliteratur\w*|\bcytuj\w*|\bisbn\b|\bdoi\b|"
    r"martw\w* link\w*|link\w* zewnętrzn\w*|refLinks|WP:REF\w*|WP:MARTWE|WP:WER\w*|weryfikowaln\w*|\bsources?\b|\bcitations?\b|"
    r"\breferenc\w+",
    re.IGNORECASE,
)


@cache
def _domains() -> dict[str, str]:
    mapping = dict(load_domain_categories())
    for category, names in REDDIT_DOMAINS.items():
        for name in names:
            mapping.setdefault(name, category)
    return mapping


@cache
def _names() -> list[tuple[str, re.Pattern]]:
    """Name patterns per category; acronyms (all capitals) match case-sensitively, the rest ignoring case."""
    patterns = []
    for category, alternatives in NAMES.items():
        exact = [part for part in alternatives.split("|") if part.isupper()]
        loose = [part for part in alternatives.split("|") if not part.isupper()]
        if exact:
            patterns.append((category, re.compile(rf"\b(?:{'|'.join(exact)})\b")))
        if loose:
            patterns.append((category, re.compile(rf"\b(?:{'|'.join(loose)})\b", re.IGNORECASE)))
    return patterns


def domain_category(url: str) -> str | None:
    """Category of a link by its domain (None when it is not a source: own media, forms, user profiles)."""
    host = link_host(url)
    if not host or host in OWN_MEDIA_HOSTS or host in FORM_HOSTS or "docs.google.com/forms" in url:
        return None
    if host.endswith("reddit.com") and re.search(r"/(?:u|user)/", url):
        return None
    category = categorise(pd.Series([host]), _domains()).iloc[0]
    if category != UNCLASSIFIED:
        return category
    if BLOG_HOST.search(host):
        return "social_blog"
    if NEWS_HOST.search(host):
        return "media"
    return UNTYPED


def named_sources(text: str) -> set[str]:
    """Categories of the sources named in `text`."""
    return {category for category, pattern in _names() if pattern.search(text)}


def cited_after_cues(text: str, cue: re.Pattern) -> set[str]:
    """Categories of the sources named right after each citation cue; `unknown` for a cue without a recognisable source."""
    found = set()
    for match in cue.finditer(text):
        # The cue itself may name the source ("study shows", "przypis z").
        window = text[match.start(): match.end() + WINDOW]
        named = named_sources(window)
        if named:
            found |= named
        elif GENERIC_SOURCE.search(window) or cue is REDDIT_CUE:
            found.add("unknown")
    return found


def reddit_labels(title: str, body: str, link: str) -> set[str]:
    text = OPINION.sub(" ", f"{title}\n{body}")
    found = set()
    for url in ([link] if link else []) + URL.findall(body):
        if (category := domain_category(url)) is not None:
            found.add(category)
    found |= cited_after_cues(URL.sub(" ", text), REDDIT_CUE)
    if PERSONAL.search(text):
        found.add("personal")
    return found


def wikipedia_labels(comment: str) -> tuple[set[str], int]:
    """Source categories and `edit_about_sources` of one edit summary."""
    text = wikipedia_text(comment)
    edit = int(bool(EDIT_CUE.search(text)))
    if REVERT.search(text):
        return set(), edit
    plain = OPINION.sub(" ", TECHNICAL_LINK.sub(" ", text))
    found = set()
    for url in URL.findall(plain):
        if not link_host(url).endswith(WIKI_HOSTS) and (category := domain_category(url)) is not None:
            found.add(category)
    found |= cited_after_cues(URL.sub(" ", plain), WIKIPEDIA_CUE)
    return found, edit


def _document(codes: set[str]) -> tuple[int, str]:
    if not codes:
        return 0, NO_SOURCE
    # R5: a concrete source wins over a vague one.
    if len(codes) > 1:
        codes = codes - {"unknown"}
    return 1, LABEL_SEPARATOR.join(sorted(codes))


def labels(units: pd.DataFrame) -> pd.DataFrame:
    """Document labels of rules_v2 for units of both platforms (`gold.load_units` columns)."""
    rows = []
    frame = units.reindex(columns=["unit_id", "platform", "title", "text", "link"]).fillna("")
    for unit in frame.itertuples(index=False):
        if unit.platform == "reddit":
            codes, edit = reddit_labels(str(unit.title), str(unit.text), str(unit.link)), pd.NA
        else:
            codes, edit = wikipedia_labels(str(unit.text))
        cites, source_types = _document(codes)
        rows.append({"unit_id": str(unit.unit_id), "platform": unit.platform, "cites_source": cites,
                     "source_types": source_types, "edit_about_sources": edit})
    result = pd.DataFrame(rows, columns=LABEL_COLUMNS)
    result["edit_about_sources"] = result["edit_about_sources"].astype("Int64")
    return result
