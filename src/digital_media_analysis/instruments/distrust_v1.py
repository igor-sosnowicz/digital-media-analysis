"""Instrument distrust v1: a lexicon of phrases that express distrust of scientists and scientific institutions.

A second, independent indicator for hypothesis H1 v2 next to stance_v2. A unit
is flagged when it contains one of the phrases below as whole words, ignoring
case. The lexicon is written from the literature on science scepticism, not
from the data, and is validated against the human `consensus_stance =
challenges` labels of the H1 v2 validation sample.
"""

import re

import pandas as pd

VERSION = "distrust_v1"
PHRASES = [
    r"so[- ]called (?:experts?|scientists?|science)",
    r"(?:big|evil) pharma",
    r"follow the money",
    r"do (?:your|ur) (?:own )?research",
    r"mainstream (?:science|media|scientists?)",
    r"(?:paid|bought|corrupt) (?:off )?(?:scientists?|researchers?|experts?)",
    r"(?:climate|global warming|vaccine) (?:hoax|scam|lie|fraud)",
    r"(?:hoax|scam) of (?:climate change|global warming)",
    r"scientists? (?:are|were) (?:lying|wrong|bought)",
    r"(?:fake|junk|pseudo)[- ]?science",
    r"(?:the )?science is (?:not )?settled",
    r"wake up,? sheeple",
    r"sheeple",
    r"they don'?t want you to know",
    r"official (?:story|narrative)",
    r"medical establishment",
    r"agenda[- ]driven (?:science|research)",
]
PATTERN = re.compile(r"(?<!\w)(?:" + "|".join(f"(?:{phrase})" for phrase in PHRASES) + r")(?!\w)", re.IGNORECASE)


def labels(texts: pd.Series) -> pd.DataFrame:
    """Per unit (index of `texts` = unit_id): `distrust` 0/1 and the first phrase found."""
    found = [PATTERN.search(text or "") for text in texts.fillna("").astype(str)]
    return pd.DataFrame({
        "unit_id": texts.index.astype(str),
        "distrust": [int(match is not None) for match in found],
        "cue": [match.group(0).lower() if match else "" for match in found],
    })
