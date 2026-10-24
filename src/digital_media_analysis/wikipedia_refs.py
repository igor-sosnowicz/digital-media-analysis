"""Links added to Wikipedia references, revision by revision, with the codebook category of their domain.

For every revision of a configured page, the links inside `<ref>…</ref>` are
compared with the previous revision; a link counts as added when it appears
more often than before (a multiset difference, so moving a reference adds
nothing). Wayback Machine links are unwrapped to the archived address. The
domain's category comes from `codebook/domains.yaml` (longest matching entry);
unlisted domains stay `unclassified`. This is the measure of hypothesis H2.
"""

import json
import re
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from urllib.parse import urlsplit

import pandas as pd
import yaml

from digital_media_analysis.config_reader import get_wikipedia_pages
from digital_media_analysis.datasets import page_title
from digital_media_analysis.paths import PROJECT_ROOT, RAW_WIKIPEDIA_DIR

DOMAINS_PATH = PROJECT_ROOT / "codebook" / "domains.yaml"
UNCLASSIFIED = "unclassified"
REFERENCE = re.compile(r"<ref\b[^>/]*>(.*?)</ref>", re.IGNORECASE | re.DOTALL)
URL = re.compile(r"https?://[^\s|\]}<>\"']+", re.IGNORECASE)
ARCHIVED = re.compile(r"^https?://(?:web\.)?archive\.org/web/[^/]+/(?P<url>.+)$", re.IGNORECASE)


def normalise(url: str) -> str:
    """The archived address of a Wayback Machine link, without trailing punctuation."""
    url = url.rstrip(".,;:)")
    if match := ARCHIVED.match(url):
        url = match["url"]
        if not re.match(r"^https?://", url, re.IGNORECASE):
            url = "http://" + url.removeprefix("//")
    return url


def domain(url: str) -> str:
    return urlsplit(url).netloc.lower().split("@")[-1].split(":")[0].removeprefix("www.")


def reference_links(content: str) -> Counter:
    """Every link inside the `<ref>` tags of an article text, normalised, with its count."""
    return Counter(normalise(url) for body in REFERENCE.findall(content or "") for url in URL.findall(body))


def added_links(revisions: Iterable[tuple[str, int, str, str]]) -> pd.DataFrame:
    """Links each revision added to the references: page, revision_number, introduced, url, domain.

    `revisions` are (page, revision_number, introduced, content), in revision order within each page.
    """
    rows, previous = [], {}
    for page, number, introduced, content in revisions:
        links = reference_links(content)
        for url, count in (links - previous.get(page, Counter())).items():
            rows += [{"page": page, "revision_number": number, "introduced": introduced, "url": url, "domain": domain(url)}] * count
        previous[page] = links
    return pd.DataFrame(rows, columns=["page", "revision_number", "introduced", "url", "domain"])


def load_domain_categories(path: Path = DOMAINS_PATH) -> dict[str, str]:
    """Domain -> category from the domain list."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    mapping = {}
    for category, domains in data.items():
        if category == "version":
            continue
        for name in domains:
            if name in mapping:
                raise ValueError(f"{name} is listed under both {mapping[name]} and {category} in {path}")
            mapping[name.lower()] = category
    return mapping


def categorise(domains: pd.Series, mapping: dict[str, str]) -> pd.Series:
    """Category of each domain: the longest listed suffix that matches whole labels, else `unclassified`."""
    def lookup(name: str) -> str:
        labels = name.split(".")
        for start in range(len(labels)):
            if (candidate := ".".join(labels[start:])) in mapping:
                return mapping[candidate]
        return UNCLASSIFIED

    return domains.map(lookup)


def load_added_links(data_dir: Path = RAW_WIKIPEDIA_DIR, pages: list[str] | None = None) -> pd.DataFrame:
    """Added reference links of the configured pages, with the category of their domain and the year."""
    listed = {page_title(url) for url in (pages or get_wikipedia_pages())}
    revisions = []
    for path in sorted(data_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        page = page_title(payload["url"]) if payload.get("url") else path.stem.replace("_", " ")
        if page not in listed:
            continue
        revisions += [
            (page, number, edit.get("introduced") or "", edit.get("new_content") or "")
            for number, edit in enumerate(payload.get("edits", []), start=1)
        ]
    links = added_links(revisions)
    year = pd.to_datetime(links["introduced"], utc=True, format="ISO8601", errors="coerce").dt.year.astype("Int64")
    return links.assign(year=year, category=categorise(links["domain"], load_domain_categories()))
