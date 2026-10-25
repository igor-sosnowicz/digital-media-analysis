"""Audit of the H1-B source indicators: error rates of gliner_v1 on posts of the H1 analysis sample.

The audit sample (`scripts/08_label_h1_sample.py --audit-annotators`) draws up to
30 posts from each stratum of the predicted category, so rare categories get
enough cases. A post's weight is 1 / its inclusion probability, which makes the
rates those of the whole H1 sample. People code the posts in
`audit_<annotator>.xlsx` with the codebook; the reference label is their agreed
label, or the arbiter's.

For each indicator (`consensus`: a consensus source, `alternative`: an
alternative source, as in `config.yaml`), over all audited posts: weighted
sensitivity and specificity with bootstrap intervals within strata, and
Youden's J = sensitivity + specificity - 1. The preregistration reports the
consensus indicator only descriptively when J <= 0.2. The pooled estimate adds
the Reddit gold test split (design weights); each source's weights are rescaled
to sum to its number of posts, so both count by their size (docs/hipotezy.md,
amendments of 25.10.2026).
"""

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

from digital_media_analysis.hypotheses import error_rates, has_any, rogan_gladen
from digital_media_analysis.validation import design_weights

VALIDITY_THRESHOLD = 0.2
# Below this many audited posts with a consensus source, the gate counts as not met.
MIN_AUDIT_POSITIVES = 10
BOOTSTRAP_SAMPLES = 1000
SEED = 20261025


def audit_frame(audit_sample: pd.DataFrame, reference: pd.DataFrame) -> pd.DataFrame:
    """Audited posts with a reference label: predicted and reference `source_types`, stratum and weight 1 / inclusion."""
    predicted = audit_sample[["unit_id", "source_types", "stratum", "inclusion"]].astype({"unit_id": str})
    gold = reference.loc[reference["platform"].eq("reddit"), ["unit_id", "source_types"]].astype({"unit_id": str})
    frame = gold.merge(predicted.rename(columns={"source_types": "source_types_pred"}), on="unit_id")
    return frame.assign(weight=1 / frame["inclusion"], source="audit")[
        ["unit_id", "source", "stratum", "weight", "source_types", "source_types_pred"]
    ]


def gold_frame(reference: pd.DataFrame, predictions: pd.DataFrame, manifest: pd.DataFrame, split: str = "test") -> pd.DataFrame:
    """Reddit gold units of a split with the instrument's `source_types`, stratum and design weight."""
    gold = reference.loc[reference["platform"].eq("reddit"), ["unit_id", "platform", "source_types"]].astype({"unit_id": str})
    predicted = predictions.loc[predictions["platform"].eq("reddit"), ["unit_id", "source_types"]].astype({"unit_id": str})
    frame = gold.merge(predicted.rename(columns={"source_types": "source_types_pred"}), on="unit_id")
    frame = frame.merge(design_weights(frame, manifest), on=["unit_id", "platform"])
    frame = frame[frame["split"].eq(split)]
    return frame.assign(source=f"gold_{split}")[["unit_id", "source", "stratum", "weight", "source_types", "source_types_pred"]]


def pooled(frames: Sequence[pd.DataFrame]) -> pd.DataFrame:
    """Frames of several sources in one, each source's weights rescaled to sum to its number of posts."""
    parts = [frame.assign(weight=frame["weight"] * len(frame) / frame["weight"].sum()) for frame in frames if len(frame)]
    if not parts:
        return pd.DataFrame(columns=["unit_id", "source", "stratum", "weight", "source_types", "source_types_pred"])
    return pd.concat(parts, ignore_index=True).assign(source="pooled")


def rates(frame: pd.DataFrame, codes: Sequence[str], samples: int = BOOTSTRAP_SAMPLES, seed: int = SEED) -> dict:
    """Weighted sensitivity, specificity and Youden's J of `has_any(codes)`, with percentile bootstrap intervals within strata."""
    frame = frame.reset_index(drop=True)
    truth = has_any(frame["source_types"], codes)
    predicted = has_any(frame["source_types_pred"], codes)
    point = error_rates(truth, predicted, frame["weight"])
    rng = np.random.default_rng(seed)
    strata = [group.index.to_numpy() for _, group in frame.groupby(["source", "stratum"])]
    draws = []
    for _ in range(samples if len(frame) else 0):
        rows = np.concatenate([rng.choice(index, size=len(index), replace=True) for index in strata])
        draw = error_rates(truth.iloc[rows], predicted.iloc[rows], frame["weight"].iloc[rows])
        draws.append((draw["sensitivity"], draw["specificity"], draw["sensitivity"] + draw["specificity"] - 1))
    draws = np.array(draws, dtype=float).reshape(-1, 3)
    bounds = [np.nanquantile(draws[:, column], [0.025, 0.975]) if np.isfinite(draws[:, column]).any() else (np.nan, np.nan)
              for column in range(3)]
    youden = point["sensitivity"] + point["specificity"] - 1
    return {
        "sensitivity": point["sensitivity"], "sensitivity_low": bounds[0][0], "sensitivity_high": bounds[0][1],
        "specificity": point["specificity"], "specificity_low": bounds[1][0], "specificity_high": bounds[1][1],
        "youden": youden, "youden_low": bounds[2][0], "youden_high": bounds[2][1],
        "valid": bool(youden > VALIDITY_THRESHOLD) if np.isfinite(youden) else False,
        "positives": point["positives"], "negatives": point["negatives"], "posts": len(frame),
    }


def rate_table(frames: Mapping[str, pd.DataFrame], indicators: Mapping[str, Sequence[str]], samples: int = BOOTSTRAP_SAMPLES) -> pd.DataFrame:
    """Error rates per source (e.g. audit, gold_test, pooled) and indicator."""
    rows = [{"source": source, "indicator": indicator, **rates(frame, codes, samples)}
            for source, frame in frames.items() for indicator, codes in indicators.items()]
    return pd.DataFrame(rows)


def corrected_shares(yearly: pd.DataFrame, table: pd.DataFrame, source: str = "pooled") -> pd.DataFrame:
    """Rogan-Gladen corrected yearly shares (and bounds) of the H1-B indicators, from the error rates of `source`.

    The bounds carry the sampling error of the observed share only, not that of
    the error rates (the correction is increasing in the observed share when J > 0).
    """
    chosen = table[table["source"].eq(source)].set_index("indicator")
    shares = yearly[yearly["hypothesis"].eq("H1-B") & yearly["outcome"].isin(chosen.index)].copy()
    for column in ["share", "low", "high"]:
        shares[f"corrected_{column}"] = [
            rogan_gladen(value, chosen.loc[outcome, "sensitivity"], chosen.loc[outcome, "specificity"])
            for value, outcome in zip(shares[column], shares["outcome"])
        ]
    return shares.assign(rates_from=source)
