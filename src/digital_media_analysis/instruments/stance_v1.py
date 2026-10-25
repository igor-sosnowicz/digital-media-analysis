"""Instrument stance v1: zero-shot NLI for `consensus_stance` of Reddit posts (codebook 2.1, rule R14).

The multilingual NLI model scores three hypotheses for each post: that it is
about science at all (`relevance`), that the author trusts science (`supports`)
and that the author distrusts it or rejects the consensus (`challenges`). A post
below the relevance threshold is `not_applicable`; otherwise it is `challenges`
when that score reaches its threshold and is not lower than `supports`, then
`supports` when that score reaches its threshold, and `neutral` otherwise.

The thresholds must be tuned on human stance labels of the dev split before
the instrument may be used for hypothesis H1-A; until then `TUNED` is False and
the confirmatory analysis refuses to run it.
"""

import pandas as pd

from digital_media_analysis.instruments import nli
from digital_media_analysis.instruments.unit_text import unit_texts

VERSION = "stance_v1"
MODEL, REVISION = nli.MODEL, nli.REVISION
HYPOTHESES = {
    "relevance": "This text is about science, scientists, scientific research or a scientific claim.",
    "supports": "The author trusts science or scientists and treats scientific findings as reliable.",
    "challenges": "The author distrusts scientists or science, or claims that the scientific consensus is wrong.",
}

# Not tuned yet: set from the dev split once human stance labels exist, then TUNED = True.
TUNED = False
THRESHOLDS = {"relevance": 0.5, "supports": 0.5, "challenges": 0.5}


def score(units: pd.DataFrame, batch_size: int = 16) -> pd.DataFrame:
    """Entailment probability of every hypothesis for every post: unit_id, relevance, supports, challenges."""
    texts = unit_texts(units)
    unit_ids = list(units["unit_id"].astype(str))
    pairs = [(unit_id, target) for unit_id in unit_ids for target in HYPOTHESES]
    scores = nli.entailment([texts[unit_id] for unit_id, _ in pairs], [HYPOTHESES[target] for _, target in pairs],
                            batch_size=batch_size, desc=f"{VERSION} NLI batches")
    long = pd.DataFrame(pairs, columns=["unit_id", "target"]).assign(score=scores)
    return long.pivot(index="unit_id", columns="target", values="score").reindex(unit_ids).reset_index()


def labels(scores: pd.DataFrame, thresholds: dict[str, float] | None = None) -> pd.DataFrame:
    """`consensus_stance` per post from `score` output: unit_id, consensus_stance."""
    thresholds = thresholds or THRESHOLDS

    def decide(row) -> str:
        if row["relevance"] < thresholds["relevance"]:
            return "not_applicable"
        if row["challenges"] >= thresholds["challenges"] and row["challenges"] >= row["supports"]:
            return "challenges"
        if row["supports"] >= thresholds["supports"]:
            return "supports"
        return "neutral"

    return pd.DataFrame({"unit_id": scores["unit_id"].astype(str), "consensus_stance": scores.apply(decide, axis=1)})
