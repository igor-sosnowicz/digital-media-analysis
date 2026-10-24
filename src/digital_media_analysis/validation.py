"""Validate instruments against the gold standard: weighted metrics with stratified bootstrap intervals.

Every gold unit carries its design weight within the coded part of the sample:
N_h (frame units of its stratum) / n_h (imported gold units of that stratum and
split). The coded units are a random part of each stratum (annotators take the
workbook rows in their random order), so a split coded only in part still
estimates the frame.

Metrics, per platform, split and annotator subset:
- `cites_source` and `edit_about_sources`: weighted precision, recall, F1 and
  accuracy, and Cohen's kappa;
- every source category, one against the rest: weighted precision, recall and
  F1; judged only with at least `MIN_SUPPORT` gold positives;
- the label set: weighted mean MASI similarity and exact-match share, and the
  macro-F1 over the categories with enough support.
Intervals are percentile bootstrap intervals that resample units within strata.
"""

from collections.abc import Sequence

import numpy as np
import pandas as pd

from digital_media_analysis.agreement import masi_distance
from digital_media_analysis.codebook import NO_SOURCE
from digital_media_analysis.instruments.labels import LABEL_SEPARATOR

MIN_SUPPORT = 10
BOOTSTRAP_SAMPLES = 1000
CONFIDENCE = 0.95
SEED = 20261024
BINARY = ["cites_source", "edit_about_sources"]
TOO_FEW = "za mało przypadków"


def design_weights(units: pd.DataFrame, manifest: pd.DataFrame) -> pd.DataFrame:
    """`units` (unit_id, platform) with split, stratum and the weight N_h / coded units of the stratum and split."""
    design = manifest[["unit_id", "platform", "split", "stratum", "N_h"]].astype({"unit_id": str})
    joined = units[["unit_id", "platform"]].astype({"unit_id": str}).merge(design, on=["unit_id", "platform"], how="left")
    if joined["split"].isna().any():
        missing = joined.loc[joined["split"].isna(), "unit_id"].tolist()
        raise ValueError(f"{len(missing)} units are not in the manifest, e.g. {missing[:3]}")
    coded = joined.groupby(["platform", "split", "stratum"])["unit_id"].transform("size")
    return joined.assign(weight=joined["N_h"] / coded)


def label_sets(source_types: pd.Series) -> pd.Series:
    return source_types.fillna("").map(lambda text: frozenset(code for code in str(text).split(LABEL_SEPARATOR) if code))


def paired(reference: pd.DataFrame, predictions: pd.DataFrame, manifest: pd.DataFrame) -> pd.DataFrame:
    """Gold and instrument labels side by side for the units both have, with design weights."""
    gold = reference[["unit_id", "platform", "annotator", *BINARY, "source_types"]].astype({"unit_id": str})
    predicted = predictions[["unit_id", "platform", *BINARY, "source_types"]].astype({"unit_id": str})
    frame = gold.merge(predicted, on=["unit_id", "platform"], suffixes=("", "_pred"))
    frame = frame.merge(design_weights(frame, manifest), on=["unit_id", "platform"])
    return frame.assign(gold_set=label_sets(frame["source_types"]), pred_set=label_sets(frame["source_types_pred"]))


def _binary(y: np.ndarray, p: np.ndarray, w: np.ndarray) -> dict[str, float]:
    tp, fp, fn = (w * (y & p)).sum(), (w * (~y & p)).sum(), (w * (y & ~p)).sum()
    precision = tp / (tp + fp) if tp + fp else np.nan
    recall = tp / (tp + fn) if tp + fn else np.nan
    f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else np.nan
    return {"precision": precision, "recall": recall, "f1": f1}


def _kappa(y: np.ndarray, p: np.ndarray) -> float:
    observed = np.mean(y == p)
    expected = np.mean(y) * np.mean(p) + np.mean(~y) * np.mean(~p)
    return (observed - expected) / (1 - expected) if expected < 1 else np.nan


def metrics(frame: pd.DataFrame, categories: Sequence[str]) -> dict[tuple[str, str], float]:
    """Point estimates of every metric for one group of paired labels."""
    w = frame["weight"].to_numpy(float)
    results = {}
    for variable in BINARY:
        present = frame[variable].notna() & frame[f"{variable}_pred"].notna()
        if not present.any():
            continue
        y = frame.loc[present, variable].astype(int).to_numpy().astype(bool)
        p = frame.loc[present, f"{variable}_pred"].astype(int).to_numpy().astype(bool)
        weights = w[present.to_numpy()]
        for name, value in _binary(y, p, weights).items():
            results[(variable, name)] = value
        results[(variable, "accuracy")] = (weights * (y == p)).sum() / weights.sum()
        results[(variable, "kappa")] = _kappa(y, p)
    gold, predicted = list(frame["gold_set"]), list(frame["pred_set"])
    for code in categories:
        y = np.array([code in labels for labels in gold])
        p = np.array([code in labels for labels in predicted])
        for name, value in _binary(y, p, w).items():
            results[(f"source_types:{code}", name)] = value
    similarity = np.array([1 - masi_distance(g, q) for g, q in zip(gold, predicted)])
    results[("source_types", "masi")] = (w * similarity).sum() / w.sum()
    results[("source_types", "exact_match")] = (w * np.array([g == q for g, q in zip(gold, predicted)])).sum() / w.sum()
    return results


def _support(frame: pd.DataFrame, variable: str) -> int:
    if variable in BINARY:
        return int(frame[variable].fillna(0).astype(int).sum())
    if variable.startswith("source_types:"):
        code = variable.split(":", 1)[1]
        return int(sum(code in labels for labels in frame["gold_set"]))
    return len(frame)


def _with_macro(values: dict, frame: pd.DataFrame, categories: Sequence[str]) -> dict:
    judged = [code for code in categories if _support(frame, f"source_types:{code}") >= MIN_SUPPORT]
    scores = [values.get((f"source_types:{code}", "f1"), np.nan) for code in judged]
    values[("source_types", "macro_f1")] = float(np.nanmean(scores)) if judged and not np.all(np.isnan(scores)) else np.nan
    return values


def _bootstrap(frame: pd.DataFrame, categories: Sequence[str], samples: int, seed: int) -> pd.DataFrame:
    """Metric values over bootstrap replicates that resample units within strata."""
    rng = np.random.default_rng(seed)
    strata = [group.index.to_numpy() for _, group in frame.groupby("stratum")]
    replicates = []
    for _ in range(samples):
        rows = np.concatenate([rng.choice(index, size=len(index), replace=True) for index in strata])
        sample = frame.loc[rows]
        replicates.append(_with_macro(metrics(sample, categories), sample, categories))
    return pd.DataFrame(replicates)


def evaluate(
    reference: pd.DataFrame,
    predictions: pd.DataFrame,
    manifest: pd.DataFrame,
    instrument: str,
    categories: Sequence[str],
    samples: int = BOOTSTRAP_SAMPLES,
    seed: int = SEED,
) -> pd.DataFrame:
    """Long table of metrics per platform, split and subset (`all` and each annotator)."""
    categories = [code for code in categories if code != NO_SOURCE]
    frame = paired(reference, predictions, manifest)
    rows = []
    alpha = (1 - CONFIDENCE) / 2
    for (platform, split), group in frame.groupby(["platform", "split"]):
        subsets = {"all": group, **{annotator: part for annotator, part in group.groupby("annotator")}}
        for subset, part in subsets.items():
            part = part.reset_index(drop=True)
            values = _with_macro(metrics(part, categories), part, categories)
            draws = _bootstrap(part, categories, samples, seed) if samples else pd.DataFrame()
            for (variable, metric), value in values.items():
                support = _support(part, variable)
                low = high = np.nan
                if (variable, metric) in draws and draws[(variable, metric)].notna().any():
                    low, high = np.nanquantile(draws[(variable, metric)].astype(float), [alpha, 1 - alpha])
                rows.append({
                    "instrument": instrument, "platform": platform, "split": split, "subset": subset,
                    "variable": variable, "metric": metric, "value": value, "low": low, "high": high,
                    "support": support, "units": len(part),
                    "note": TOO_FEW if variable.startswith("source_types:") and support < MIN_SUPPORT else "",
                })
    return pd.DataFrame(rows)


def confusion(reference: pd.DataFrame, predictions: pd.DataFrame, manifest: pd.DataFrame, instrument: str) -> pd.DataFrame:
    """Unweighted confusion counts of `cites_source` per platform and split."""
    frame = paired(reference, predictions, manifest)
    y = frame["cites_source"].astype(int).astype(bool)
    p = frame["cites_source_pred"].astype(int).astype(bool)
    counts = frame.assign(tp=y & p, fp=~y & p, fn=y & ~p, tn=~y & ~p).groupby(["platform", "split"])[["tp", "fp", "fn", "tn"]].sum()
    return counts.reset_index().assign(instrument=instrument)


def objective(reference: pd.DataFrame, predictions: pd.DataFrame, manifest: pd.DataFrame, categories: Sequence[str]) -> dict:
    """Point estimates used for tuning: weighted MASI, cites_source F1 and edit_about_sources F1."""
    frame = paired(reference, predictions, manifest)
    values = metrics(frame, [code for code in categories if code != NO_SOURCE])
    return {
        "masi": values[("source_types", "masi")],
        "cites_f1": values.get(("cites_source", "f1"), np.nan),
        "edit_f1": values.get(("edit_about_sources", "f1"), np.nan),
    }


def nominal_metrics(truth: pd.Series, predicted: pd.Series, weights: pd.Series, classes: Sequence[str]) -> dict[str, float]:
    """Weighted accuracy, per-class precision, recall and F1, macro-F1 and Cohen's kappa of a nominal variable."""
    y, p, w = truth.astype(str).to_numpy(), predicted.astype(str).to_numpy(), weights.to_numpy(float)
    results = {"accuracy": (w * (y == p)).sum() / w.sum()}
    f1s = []
    for name in classes:
        for metric, value in _binary(y == name, p == name, w).items():
            results[f"{name}:{metric}"] = value
        if (y == name).any():
            f1s.append(results[f"{name}:f1"])
    results["macro_f1"] = float(np.nanmean(f1s)) if f1s else np.nan
    observed = np.mean(y == p)
    expected = sum(np.mean(y == name) * np.mean(p == name) for name in classes)
    results["kappa"] = (observed - expected) / (1 - expected) if expected < 1 else np.nan
    return results

