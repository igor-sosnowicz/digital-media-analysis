"""Revision histories of the H2 v2 frame: references per revision, reverts, and links added and removed.

The download keeps, for each revision, its metadata (id, parent, time, editor,
whether the editor is anonymous, SHA-1 of the text, tags, summary) and the
links inside its `<ref>` tags with their counts, not the article text, so
hundreds of pages fit on a disk. One revision before the baseline period is
kept as the starting state.

Reverts: a revision whose SHA-1 equals that of an earlier revision restores it,
so the revisions in between were reverted (identity reverts, as MediaWiki's
`mw-reverted` tag); revisions tagged `mw-reverted` count as well.

Link events: a link is added when it appears more often than in the previous
revision (multiset difference, as `wikipedia_refs.added_links`). Each addition
records whether it is the link's first addition to the page in the observed
history, whether it came in a revision that was later reverted, and how long
the link stayed: until the first later revision without it (censored at the
end of the data).
"""

import gzip
import json
from collections import Counter
from collections.abc import Callable, Iterable, Iterator
from datetime import datetime
from pathlib import Path

import pandas as pd

from digital_media_analysis.instruments.refs_v1 import references
from digital_media_analysis.wikipedia_refs import URL, domain, normalise, reference_links

RVPROP = "ids|timestamp|user|userid|sha1|tags|comment|size|content"
REVERTED_TAG = "mw-reverted"


def revision_record(page: dict, revision: dict) -> dict:
    """The kept fields of one API revision, with its links and number of references.

    Articles keep the links inside `<ref>` tags; talk pages (namespace 1), where
    editors propose sources in plain text, keep every link.
    """
    slot = revision.get("slots", {}).get("main", {})
    content = slot.get("content", "") if not slot.get("texthidden") else ""
    links = reference_links(content) if page.get("ns", 0) != 1 else Counter(normalise(url) for url in URL.findall(content))
    return {
        "pageid": page["pageid"], "ns": page.get("ns", 0), "title": page["title"],
        "revid": revision["revid"], "parentid": revision.get("parentid", 0), "timestamp": revision["timestamp"],
        "user": revision.get("user", ""), "anon": bool(revision.get("anon", False)) or revision.get("userid", 1) == 0,
        "sha1": revision.get("sha1", ""), "tags": revision.get("tags", []), "comment": revision.get("comment", ""),
        "size": revision.get("size", 0), "links": dict(links), "refs": sum(references(content).values()),
    }


def fetch_history(get: Callable[[dict], dict], title: str, start: str, end: str) -> Iterator[dict]:
    """Records of the last revision before `start` and of every revision in [start, end), oldest first."""
    base = {"action": "query", "prop": "revisions", "titles": title, "rvprop": RVPROP, "rvslots": "main"}
    before = get({**base, "rvstart": start, "rvdir": "older", "rvlimit": 1})
    for page in before.get("query", {}).get("pages", []):
        for revision in page.get("revisions", []):
            if revision["timestamp"] < start:
                yield revision_record(page, revision)
    params = {**base, "rvstart": start, "rvend": end, "rvdir": "newer", "rvlimit": "max"}
    while True:
        data = get(params)
        for page in data.get("query", {}).get("pages", []):
            for revision in page.get("revisions", []):
                if revision["timestamp"] < end:
                    yield revision_record(page, revision)
        if "continue" not in data:
            break
        params = {**params, **data["continue"]}


def save_records(records: Iterable[dict], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with gzip.open(path, "wt", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return count


def load_records(paths: Iterable[Path]) -> list[dict]:
    records = []
    for path in paths:
        with gzip.open(path, "rt", encoding="utf-8") as file:
            records += [json.loads(line) for line in file]
    return records


def mark_reverts(revisions: list[dict], window: int = 15) -> list[bool]:
    """Per revision (one page, oldest first): whether it was reverted, by tag or by a later identity revert within `window`."""
    reverted = [REVERTED_TAG in (revision.get("tags") or []) for revision in revisions]
    last_seen: dict[str, int] = {}
    for index, revision in enumerate(revisions):
        sha1 = revision.get("sha1") or ""
        earlier = last_seen.get(sha1)
        if sha1 and earlier is not None and 1 <= index - earlier - 1 <= window:
            for between in range(earlier + 1, index):
                reverted[between] = True
        if sha1:
            last_seen[sha1] = index
    return reverted


def link_events(revisions: list[dict], end: str) -> pd.DataFrame:
    """Every link addition of one page (revisions oldest first, the first one is the starting state).

    Columns: pageid, ns, title, revid, timestamp, user, anon, url, domain, first_addition,
    reverted_edit, removed_at, days_present, censored.
    """
    reverted = mark_reverts(revisions)
    rows, ever, open_rows = [], set(), {}
    previous = Counter(revisions[0]["links"]) if revisions else Counter()
    ever.update(previous)
    for index, revision in enumerate(revisions[1:], start=1):
        current = Counter(revision["links"])
        for url in list(open_rows):
            if current[url] == 0:
                for row in open_rows.pop(url):
                    row["removed_at"] = revision["timestamp"]
        for url, count in (current - previous).items():
            for _ in range(count):
                row = {
                    "pageid": revision["pageid"], "ns": revision["ns"], "title": revision["title"], "revid": revision["revid"],
                    "timestamp": revision["timestamp"], "user": revision["user"], "anon": revision["anon"], "url": url,
                    "domain": domain(url), "first_addition": url not in ever, "reverted_edit": reverted[index], "removed_at": None,
                }
                rows.append(row)
                open_rows.setdefault(url, []).append(row)
            ever.add(url)
        previous = current
    table = pd.DataFrame(rows, columns=["pageid", "ns", "title", "revid", "timestamp", "user", "anon", "url", "domain",
                                        "first_addition", "reverted_edit", "removed_at"])
    added = pd.to_datetime(table["timestamp"], utc=True)
    removed = pd.to_datetime(table["removed_at"], utc=True)
    stop = pd.Timestamp(datetime.fromisoformat(end))
    return table.assign(
        censored=table["removed_at"].isna(),
        days_present=((removed.fillna(stop) - added).dt.total_seconds() / 86400).clip(lower=0),
    )


def revisions_by_page(records: list[dict]) -> dict[tuple[int, int], list[dict]]:
    """Records grouped by (pageid, ns), oldest first."""
    pages: dict[tuple[int, int], list[dict]] = {}
    for record in records:
        pages.setdefault((record["pageid"], record["ns"]), []).append(record)
    return {key: sorted(revisions, key=lambda revision: (revision["timestamp"], revision["revid"])) for key, revisions in pages.items()}
