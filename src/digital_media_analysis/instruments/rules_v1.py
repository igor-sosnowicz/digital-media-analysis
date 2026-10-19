"""Instrument v1: keyword and regex source-reference extractor, frozen as the baseline.

This is a verbatim move of the extractors that lived in `notebooks/Reditt_EDA.ipynb`
and `notebooks/Wikipedia_EDA.ipynb` (state of commit bd46695). Do not fix its rules
here: validation compares later instruments against exactly this behaviour, including
its known errors. Improvements belong in a new instrument version.

The two platforms use different category schemes; `REDDIT_CATEGORY_MAP` and
`WIKIPEDIA_CATEGORY_MAP` translate them into the shared codebook categories.
"""

import re
from urllib.parse import urlsplit

import pandas as pd

VERSION = "v1"

# --- Reddit ------------------------------------------------------------------

REDDIT_REFERENCE_PATTERNS = {
    "media informacyjne": ["tvn", "tvp", "polsat", "gazeta wyborcza", "rzeczpospolita", "onet", "wp.pl", "interia", "gazeta.pl", "rmf24", "radio zet", "bbc", "reuters", "the guardian"],
    "źródła oficjalne": ["gov.pl", "sejm", "senat", "gmina", "urząd miasta", "policja", "ministerstwo", "główny urząd statystyczny", "gus", "zus", "nfz"],
    "nauka i medycyna": ["pubmed", "doi.org", "nature.com", "science.org", "badania", "badanie", "artykuł naukowy", "metaanaliza", "lekarz", "klinika"],
    "platformy i media społecznościowe": ["youtube", "facebook", "instagram", "tiktok", "twitter", "x.com", "wykop", "reddit"],
    "encyklopedie i bazy wiedzy": ["wikipedia", "wikidata", "imdb", "tripadvisor", "google maps"],
    "źródła komercyjne": ["allegro", "olx", "amazon", "booking", "opinie google", "strona producenta", "sklep"],
    "źródła osobiste i społecznościowe": ["u mnie", "mój znajomy", "znajomy", "kolega", "koleżanka", "z własnego doświadczenia", "osobiście", "mieszkam", "pracuję"],
}
REDDIT_SOURCE_CUES = ["według", "źródło", "źródła", "powołuję się", "czytałem", "czytałam", "przeczytałem", "przeczytałam", "badania pokazują", "dane pokazują", "jak podaje", "podano", "link", "artykuł"]
REDDIT_URL_PATTERN = re.compile(r"https?://[^\s\]\)<>\"']+|(?:www\.)?[a-z0-9][a-z0-9.-]+\.(?:pl|com|org|net|eu|gov)(?:/[^\s\]\)<>\"']*)?", re.IGNORECASE)
REDDIT_TEXT_COLUMNS = ["comment", "comment_text", "body", "text"]


def extract_reddit_mentions(text: object) -> list[dict]:
    """Return every source mention v1 finds in one Reddit text."""
    text = "" if pd.isna(text) else str(text)
    lowered = text.casefold()
    found = []
    urls = REDDIT_URL_PATTERN.findall(text)
    for url in urls:
        domain = re.sub(r"^https?://", "", url, flags=re.IGNORECASE).split("/")[0].lower()
        found.append({"reference": domain, "category": "link/domena", "confidence": 1.0})
    for category, terms in REDDIT_REFERENCE_PATTERNS.items():
        for term in terms:
            if term in lowered:
                found.append({"reference": term, "category": category, "confidence": 0.85})
    cue_count = sum(cue in lowered for cue in REDDIT_SOURCE_CUES)
    if cue_count and not found:
        found.append({"reference": "niesprecyzowane źródło", "category": "sygnał powołania", "confidence": 0.55})
    return found


def extract_reddit_references(df: pd.DataFrame, text_column: str | None = None) -> pd.DataFrame:
    """Run v1 over Reddit posts; one row per (post row, reference, category).

    Without `text_column`, the first available of `REDDIT_TEXT_COLUMNS` is used,
    falling back to `title`, as in the original notebook.
    """
    if text_column is None:
        text_columns = [column for column in REDDIT_TEXT_COLUMNS if column in df.columns]
        text_column = text_columns[0] if text_columns else "title"
    reference_rows = []
    for row_index, text in df[text_column].items():
        for reference in extract_reddit_mentions(text):
            reference_rows.append({
                "row_index": row_index,
                "subreddit": df.loc[row_index, "subreddit"],
                "score": df.loc[row_index, "score"],
                "num_comments": df.loc[row_index, "num_comments"],
                "text_preview": re.sub(r"\s+", " ", str(text))[:220],
                **reference,
            })
    references = pd.DataFrame(reference_rows, columns=[
        "row_index", "subreddit", "score", "num_comments", "text_preview",
        "reference", "category", "confidence",
    ])
    return references.drop_duplicates(["row_index", "reference", "category"])


# --- Wikipedia ---------------------------------------------------------------

WIKIPEDIA_SOURCE_CATEGORIES = {
    "instytucje publiczne": ["gov.pl", "who.int", "ecdc.europa.eu", "aids.gov.pl", "nfz", "gis", "gus", "ministerstwo", "urząd"],
    "nauka i edukacja": ["doi.org", "pubmed", "nature.com", "science.org", "academia.edu", "pwn.pl", "uniwersytet", "uniwersytetu", "instytut"],
    "media": ["gazeta", "tvn", "tvp", "polsat", "onet", "wp.pl", "interia", "bbc", "reuters", "guardian"],
    "organizacje społeczne i środowiskowe": ["wwf", "greenpeace", "fundacja", "stowarzyszenie", "ngo"],
    "źródła encyklopedyczne": ["wikipedia.org", "wikimedia.org", "wikiwand"],
    "źródła osobiste": ["moje doświadczenie", "z własnego doświadczenia", "widziałem", "widziałam", "pamiętam", "mój przypadek", "użytkownik"],
}
WIKIPEDIA_SOURCE_CUES = re.compile(r"\b(według|źródło|źródła|badania|badanie|raport|dane|artykuł|publikacja|jak podaje|podaje|link|cytuję|opublikowano)\b", re.IGNORECASE)
WIKIPEDIA_URL_PATTERN = re.compile(r"https?://[^\s\]})>,]+", re.IGNORECASE)
WIKIPEDIA_SHORTCUT_PATTERN = re.compile(r"\[\[(?P<namespace>WP|WPT|WT):(?P<title>[^\]|]+)(?:\|[^\]]*)?\]\]", re.IGNORECASE)


def classify_wikipedia_source(reference: str, domain: str, comment: str) -> tuple[str, float]:
    """Return v1's (category, heuristic confidence) for one Wikipedia mention.

    The whole edit summary is part of the matched text, so words elsewhere in the
    comment can decide the category of an unrelated reference.
    """
    haystack = f"{reference} {domain} {comment}".casefold()
    for category, terms in WIKIPEDIA_SOURCE_CATEGORIES.items():
        if any(term.casefold() in haystack for term in terms):
            return category, 0.90
    if domain:
        return "inna domena zewnętrzna", 0.80
    if WIKIPEDIA_SOURCE_CUES.search(comment):
        return "powołanie bez wskazanego źródła", 0.55
    return "odniesienie techniczne Wikipedii", 0.95


def extract_wikipedia_references(df: pd.DataFrame) -> pd.DataFrame:
    """Run v1 over Wikipedia edit summaries; one row per (revision, reference, category).

    `df` needs the columns `page`, `revision_number` and `comment`.
    """
    semantic_references = []
    comment_mask = df["comment"].fillna("").astype(str).str.strip().ne("")
    for row in df.loc[comment_mask].itertuples(index=False):
        comment = row.comment
        matches = [(match, "url") for match in WIKIPEDIA_URL_PATTERN.finditer(comment)]
        matches += [(match, "wiki") for match in WIKIPEDIA_SHORTCUT_PATTERN.finditer(comment)]
        if not matches and WIKIPEDIA_SOURCE_CUES.search(comment):
            category, confidence = classify_wikipedia_source("", "", comment)
            semantic_references.append({"page": row.page, "revision_number": row.revision_number, "comment": comment, "reference": "niesprecyzowane źródło", "domain": "", "source_category": category, "confidence": confidence, "cue": WIKIPEDIA_SOURCE_CUES.search(comment).group(0)})
        for match, match_type in matches:
            if match_type == "url":
                reference = match.group(0).rstrip(".,;:!?\"")
                domain = urlsplit(reference).netloc.lower().removeprefix("www.")
            else:
                reference = f"{match.group('namespace').upper()}:{match.group('title').strip()}"
                domain = "wikipedia.org"
            cue_match = WIKIPEDIA_SOURCE_CUES.search(comment)
            category, confidence = classify_wikipedia_source(reference, domain, comment)
            semantic_references.append({"page": row.page, "revision_number": row.revision_number, "comment": comment, "reference": reference, "domain": domain, "source_category": category, "confidence": confidence, "cue": cue_match.group(0) if cue_match else ""})

    references = pd.DataFrame(semantic_references, columns=[
        "page", "revision_number", "comment", "reference", "domain",
        "source_category", "confidence", "cue",
    ])
    return references.drop_duplicates(["page", "revision_number", "reference", "source_category"])


# --- Mapping to codebook categories --------------------------------------------
# A value of None means "v1 detected a reference but assigns no codebook type"
# (it still counts towards `cites_source`). Categories listed in the
# *_NON_CITATION sets are, by v1's own definition, not source references.
# A v1 category that mixes codebook categories maps to the one most of its
# terms belong to; validation measures the rest as v1 errors.

REDDIT_CATEGORY_MAP: dict[str, str | None] = {
    # Every URL, next to any keyword category of the same link.
    "link/domena": None,
    "media informacyjne": "media",
    # Mostly offices and administration (gov.pl, sejm, gmina, policja, ZUS); only GUS is statistical.
    "źródła oficjalne": "other",
    "nauka i medycyna": "scientific",
    "platformy i media społecznościowe": "social_blog",
    "encyklopedie i bazy wiedzy": "encyclopedia",
    "źródła komercyjne": "other",
    "źródła osobiste i społecznościowe": "personal",
    "sygnał powołania": "unknown",
}
REDDIT_NON_CITATION: frozenset[str] = frozenset()

WIKIPEDIA_CATEGORY_MAP: dict[str, str | None] = {
    # Mostly health and statistical bodies (WHO, ECDC, GIS, GUS); gov.pl, ministries and offices are `other`.
    "instytucje publiczne": "institutional",
    "nauka i edukacja": "scientific",
    "media": "media",
    "organizacje społeczne i środowiskowe": "other",
    "źródła encyklopedyczne": "encyclopedia",
    "źródła osobiste": "personal",
    "inna domena zewnętrzna": "other",
    "powołanie bez wskazanego źródła": "unknown",
}
WIKIPEDIA_NON_CITATION: frozenset[str] = frozenset({"odniesienie techniczne Wikipedii"})
