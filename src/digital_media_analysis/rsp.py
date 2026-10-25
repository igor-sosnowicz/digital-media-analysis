"""English Wikipedia's list of perennial sources: a third, external definition of an unreliable source for H2 v2.

The list ("Wikipedia:Reliable sources/Perennial sources") rates sources the
community discusses again and again: generally reliable (gr), no consensus
(nc), generally unreliable (gu), deprecated (d) or blacklisted (b). Each table
row carries a status template and the source's domains in a uses template.
`parse` reads them from the page's wikitext; the parsed table is saved with
the download date (codebook/rsp_domains.csv) and checked by hand once, as the
page's templates may change. A domain matches itself and its subdomains.
"""

import re
from pathlib import Path

import pandas as pd

from digital_media_analysis.paths import PROJECT_ROOT

RSP_PATH = PROJECT_ROOT / "codebook" / "rsp_domains.csv"
PAGE = "Wikipedia:Reliable sources/Perennial sources"
STATUS = re.compile(r"\{\{\s*/?\s*(?:WP:RSPSTATUS|RSPSTATUS|Status)\s*\|\s*([a-z]+)", re.IGNORECASE)
USES = re.compile(r"\{\{\s*(?:WP:RSPUSES|RSPUSES|/Uses)\s*\|([^}]*)\}\}", re.IGNORECASE)
STATUS_NAMES = {"gr": "generally reliable", "nc": "no consensus", "gu": "generally unreliable", "d": "deprecated", "b": "blacklisted"}


def parse(wikitext: str) -> pd.DataFrame:
    """Domain and status of every table row that has both a status and a uses template."""
    rows = []
    for block in re.split(r"\n\|-", wikitext):
        statuses = [match.lower() for match in STATUS.findall(block) if match.lower() in STATUS_NAMES]
        if not statuses:
            continue
        # A row with several statuses (e.g. reliable before a year, unreliable after) counts by its worst one.
        status = max(statuses, key=list(STATUS_NAMES).index)
        for uses in USES.findall(block):
            for name in uses.split("|"):
                name = name.strip().lower().removeprefix("www.")
                if "=" not in name and "." in name:
                    rows.append({"domain": name, "status": status})
    return pd.DataFrame(rows, columns=["domain", "status"]).drop_duplicates("domain", keep="last").reset_index(drop=True)


def load(path: Path = RSP_PATH) -> dict[str, str]:
    table = pd.read_csv(path)
    return dict(zip(table["domain"].str.lower(), table["status"]))


def status_of(domains: pd.Series, statuses: dict[str, str]) -> pd.Series:
    """Status of each domain by its longest listed suffix; '' when not listed."""
    def lookup(name: str) -> str:
        labels = name.split(".")
        for start in range(len(labels)):
            if (candidate := ".".join(labels[start:])) in statuses:
                return statuses[candidate]
        return ""

    return domains.fillna("").astype(str).map(lookup)
