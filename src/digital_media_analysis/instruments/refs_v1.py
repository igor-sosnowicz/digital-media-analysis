"""Instrument I4 (refs_v1): `edit_about_sources` from what an edit did to the article's references.

Wikipedia only. The references of each revision are compared with those of the
previous revision of the page (any revision, also one without an edit
summary): the bodies of `<ref>…</ref>` tags with whitespace normalised, and
`{{Cytuj …}}` templates outside them (bibliography lists). An edit is about
sources when at least `THRESHOLD` references were added or removed. The
comparison is a multiset difference, so moving a reference changes nothing.

The codebook variable records what the edit summary declares (R10), while this
instrument reads what the edit changed; an edit that adds a reference under a
summary silent about it counts as a disagreement in validation. The
instrument measures neither `cites_source` nor `source_types`.
"""

import json
import re
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

import pandas as pd

from digital_media_analysis.config_reader import get_wikipedia_pages
from digital_media_analysis.datasets import page_title
from digital_media_analysis.paths import RAW_WIKIPEDIA_DIR
from digital_media_analysis.wikipedia_refs import REFERENCE

# Chosen on the dev split (scripts/07_validate_instruments.py --tune): the fewest references added or removed.
THRESHOLD = 1
GRID = [1, 2, 3, 5, 10]
CITE_TEMPLATE = re.compile(r"\{\{\s*cytuj\b[^{}]*\}\}", re.IGNORECASE)
RAW_COLUMNS = ["unit_id", "platform", "refs_before", "refs_after", "added", "removed"]


def references(content: str) -> Counter:
    """Every reference of an article text: `<ref>` bodies and `{{Cytuj}}` templates outside them, normalised."""
    content = content or ""
    bodies = Counter(" ".join(body.split()) for body in REFERENCE.findall(content))
    outside = REFERENCE.sub(" ", content)
    templates = Counter(" ".join(template.split()).casefold() for template in CITE_TEMPLATE.findall(outside))
    return bodies + templates


def changes(revisions: Iterable[tuple[str, int, str]], wanted: set[tuple[str, int]] | None = None) -> pd.DataFrame:
    """Per revision (page, revision_number, content; in order within each page): references before and after, added, removed.

    With `wanted`, only those (page, revision_number) pairs are returned; every
    revision is still read, as each one is the previous revision of the next.
    """
    rows, previous = [], {}
    for page, number, content in revisions:
        current = references(content)
        before = previous.get(page, Counter())
        if wanted is None or (page, number) in wanted:
            rows.append({
                "page": page, "revision_number": number,
                "refs_before": sum(before.values()), "refs_after": sum(current.values()),
                "added": sum((current - before).values()), "removed": sum((before - current).values()),
            })
        previous[page] = current
    return pd.DataFrame(rows, columns=["page", "revision_number", "refs_before", "refs_after", "added", "removed"])


def _revisions(data_dir: Path, pages: set[str]):
    for path in sorted(data_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        page = page_title(payload["url"]) if payload.get("url") else path.stem.replace("_", " ")
        if page not in pages:
            continue
        for number, edit in enumerate(payload.get("edits", []), start=1):
            yield page, number, edit.get("new_content") or ""


def score(units: pd.DataFrame, data_dir: Path = RAW_WIKIPEDIA_DIR) -> pd.DataFrame:
    """Reference changes of the Wikipedia units (unit_id `page#revision_number`), from the raw revision texts."""
    wikipedia = units[units["platform"].eq("wikipedia")]
    key = wikipedia["unit_id"].astype(str).str.rsplit("#", n=1, expand=True)
    wanted = set(zip(key[0], key[1].astype(int))) if len(wikipedia) else set()
    listed = {page_title(url) for url in get_wikipedia_pages()}
    found = changes(_revisions(data_dir, listed & {page for page, _ in wanted}), wanted)
    found = found.assign(unit_id=found["page"] + "#" + found["revision_number"].astype(str), platform="wikipedia")
    if missing := sorted(set(wikipedia["unit_id"].astype(str)) - set(found["unit_id"])):
        raise ValueError(f"{len(missing)} units have no revision in {data_dir}, e.g. {missing[:3]}")
    return found[RAW_COLUMNS]


def labels(raw: pd.DataFrame, threshold: int = THRESHOLD) -> pd.DataFrame:
    """Document labels: `edit_about_sources` = 1 when at least `threshold` references were added or removed."""
    changed = (raw["added"] + raw["removed"]).ge(threshold).astype(int)
    return pd.DataFrame({
        "unit_id": raw["unit_id"], "platform": raw["platform"],
        "cites_source": pd.array([pd.NA] * len(raw), dtype="Int64"),
        "source_types": pd.Series([pd.NA] * len(raw), dtype="object"),
        "edit_about_sources": changed.to_numpy(),
    })
