"""Instrument stance v2: `consensus_stance` toward the consensus of the unit's own topic (codebook R14, R15).

Unlike stance_v1, which asks whether a text trusts "science", stance v2 asks
the NLI model whether the text agrees with, or disputes, the consensus
statement of each topic the unit is about (codebook/topics.yaml; the topics come
from topics_v1 or from people). A unit without a topic is `not_applicable`.
With several topics, the strongest score over them decides. A unit is
`challenges` when that score reaches its threshold and is not lower than the
`supports` score, then `supports` when that score reaches its threshold, and
`neutral` otherwise.

Thresholds are tuned on the human validation labels of H1 v2 (scripts/14_label_h1_v2.py
--tune); until they are set and frozen by commit, `TUNED` is False and the
confirmatory analysis refuses to use the instrument.
"""

import pandas as pd

from digital_media_analysis.instruments import nli
from digital_media_analysis.instruments.labels import LABEL_SEPARATOR

VERSION = "stance_v2"
MODEL, REVISION = nli.MODEL, nli.REVISION
TEMPLATES = {
    "supports": "The author agrees with this: {consensus}",
    "challenges": "The author disputes or mocks this: {consensus}",
}
TUNED = False
THRESHOLDS = {"supports": 0.5, "challenges": 0.5}


def pairs(units: pd.DataFrame, topics: dict) -> pd.DataFrame:
    """One row per unit and topic it is about: unit_id, topic, text."""
    rows = []
    for unit in units.itertuples(index=False):
        for code in str(unit.topics or "").split(LABEL_SEPARATOR):
            if code in topics:
                rows.append({"unit_id": str(unit.unit_id), "topic": code, "text": str(unit.text)})
    return pd.DataFrame(rows, columns=["unit_id", "topic", "text"])


def score(units: pd.DataFrame, topics: dict, batch_size: int = 16) -> pd.DataFrame:
    """Entailment probability of `supports` and `challenges` per unit and topic (`units` need unit_id, topics, text)."""
    table = pairs(units, topics)
    premises, hypotheses, keys = [], [], []
    for row in table.itertuples(index=False):
        for target, template in TEMPLATES.items():
            premises.append(row.text)
            hypotheses.append(template.format(consensus=topics[row.topic].consensus))
            keys.append((row.unit_id, row.topic, target))
    values = nli.entailment(premises, hypotheses, batch_size=batch_size, desc=f"{VERSION} NLI batches") if keys else []
    long = pd.DataFrame(keys, columns=["unit_id", "topic", "target"]).assign(score=values)
    if long.empty:
        return pd.DataFrame(columns=["unit_id", "topic", "supports", "challenges"])
    return long.pivot_table(index=["unit_id", "topic"], columns="target", values="score").reset_index()


def labels(scores: pd.DataFrame, unit_ids: pd.Series, thresholds: dict[str, float] | None = None) -> pd.DataFrame:
    """`consensus_stance` for every unit in `unit_ids` from `score` output (units without scores: not_applicable)."""
    thresholds = thresholds or THRESHOLDS
    best = scores.groupby("unit_id")[["supports", "challenges"]].max() if len(scores) else pd.DataFrame(columns=["supports", "challenges"])

    def decide(unit_id: str) -> str:
        if unit_id not in best.index:
            return "not_applicable"
        supports, challenges = best.loc[unit_id, "supports"], best.loc[unit_id, "challenges"]
        if challenges >= thresholds["challenges"] and challenges >= supports:
            return "challenges"
        if supports >= thresholds["supports"]:
            return "supports"
        return "neutral"

    ids = unit_ids.astype(str)
    return pd.DataFrame({"unit_id": ids.to_numpy(), "consensus_stance": [decide(unit_id) for unit_id in ids]})
