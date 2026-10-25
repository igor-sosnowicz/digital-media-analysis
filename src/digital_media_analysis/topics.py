"""Consensus topics of hypothesis H1 v2 and instrument topics_v1, which finds them by keyword patterns.

A unit (post or comment) is about a topic when one of the topic's patterns
(codebook/topics.yaml) matches its text as whole words, ignoring case. The
main topic (`consensus_topic`, codebook R15) is the topic with the most
matches; ties go to the earlier topic in the file. Validation against human
`consensus_topic` labels measures how often a word is used in another sense.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

from digital_media_analysis.instruments.labels import LABEL_SEPARATOR
from digital_media_analysis.paths import PROJECT_ROOT

TOPICS_PATH = PROJECT_ROOT / "codebook" / "topics.yaml"
NO_TOPIC = "none"


@dataclass(frozen=True)
class Topic:
    code: str
    name: str
    consensus: str
    pattern: re.Pattern


def load_topics(path: Path = TOPICS_PATH) -> dict[str, Topic]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    topics = {}
    for code, entry in data["topics"].items():
        alternatives = "|".join(f"(?:{pattern})" for pattern in entry["patterns"])
        topics[code] = Topic(code, entry["name"], entry["consensus"], re.compile(rf"(?<!\w)(?:{alternatives})(?!\w)", re.IGNORECASE))
    return topics


def matches(text: str, topics: dict[str, Topic]) -> dict[str, int]:
    """Number of pattern matches of every topic found in `text`."""
    counts = {code: len(topic.pattern.findall(text or "")) for code, topic in topics.items()}
    return {code: count for code, count in counts.items() if count}


def main_topic(found: dict[str, int], topics: dict[str, Topic]) -> str:
    if not found:
        return NO_TOPIC
    order = list(topics)
    return max(found, key=lambda code: (found[code], -order.index(code)))


def label(texts: pd.Series, topics: dict[str, Topic] | None = None) -> pd.DataFrame:
    """Per unit (index of `texts` = unit_id): every topic found and the main one."""
    topics = topics or load_topics()
    found = [matches(text, topics) for text in texts.fillna("").astype(str)]
    return pd.DataFrame({
        "unit_id": texts.index.astype(str),
        "topics": [LABEL_SEPARATOR.join(code for code in topics if code in hits) for hits in found],
        "consensus_topic": [main_topic(hits, topics) for hits in found],
    })
