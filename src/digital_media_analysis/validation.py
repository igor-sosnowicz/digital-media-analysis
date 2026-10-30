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
A variable an instrument does not measure (missing predictions) gets no metrics.

For the slides: weighted shares of the categories in gold (an estimate that
needs no instrument), differential error (error rates by group), McNemar's test
of two instruments on the same units and Kendall's tau between category rankings.
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
    measured = frame["source_types_pred"].notna().to_numpy()
    if not measured.any():
        return results
    w = w[measured]
    gold = [labels for labels, keep in zip(frame["gold_set"], measured) if keep]
    predicted = [labels for labels, keep in zip(frame["pred_set"], measured) if keep]
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
    if ("source_types", "masi") not in values:
        return values
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
    """Unweighted confusion counts of `cites_source` per platform and split (none when the instrument does not measure it)."""
    frame = paired(reference, predictions, manifest)
    frame = frame[frame["cites_source_pred"].notna()]
    if frame.empty:
        return pd.DataFrame(columns=["platform", "split", "tp", "fp", "fn", "tn", "instrument"])
    y = frame["cites_source"].astype(int).astype(bool)
    p = frame["cites_source_pred"].astype(int).astype(bool)
    counts = frame.assign(tp=y & p, fp=~y & p, fn=y & ~p, tn=~y & ~p).groupby(["platform", "split"])[["tp", "fp", "fn", "tn"]].sum()
    return counts.reset_index().assign(instrument=instrument)


def objective(reference: pd.DataFrame, predictions: pd.DataFrame, manifest: pd.DataFrame, categories: Sequence[str]) -> dict:
    """Point estimates used for tuning: weighted MASI, cites_source F1 and edit_about_sources F1."""
    frame = paired(reference, predictions, manifest)
    values = metrics(frame, [code for code in categories if code != NO_SOURCE])
    return {
        "masi": values.get(("source_types", "masi"), np.nan),
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



def weighted_shares(
    reference: pd.DataFrame, manifest: pd.DataFrame, categories: Sequence[str],
    samples: int = BOOTSTRAP_SAMPLES, seed: int = SEED,
) -> pd.DataFrame:
    """Share of units citing a source and of each category in the frame, estimated from labels, per platform.

    `reference` holds labels of gold units (people or an instrument) of any
    splits; the weight of a unit is N_h over the labelled units of its stratum
    in all those splits together. Intervals are bootstrap within strata.
    """
    categories = [code for code in categories if code != NO_SOURCE]
    design = manifest[["unit_id", "platform", "stratum", "N_h"]].astype({"unit_id": str})
    frame = reference[["unit_id", "platform", "cites_source", "source_types"]].astype({"unit_id": str}).merge(
        design, on=["unit_id", "platform"]
    ).reset_index(drop=True)
    frame = frame.assign(weight=frame["N_h"] / frame.groupby(["platform", "stratum"])["unit_id"].transform("size"))
    sets = label_sets(frame["source_types"])
    indicators = pd.DataFrame({"cites_source": frame["cites_source"].astype(float).to_numpy(),
                               **{code: [float(code in labels) for labels in sets] for code in categories}})
    rng = np.random.default_rng(seed)
    alpha = (1 - CONFIDENCE) / 2
    rows = []
    for platform, part in frame.groupby("platform"):
        w = part["weight"].to_numpy(float)
        values = indicators.loc[part.index].to_numpy()
        point = (w[:, None] * values).sum(axis=0) / w.sum()
        strata = [np.flatnonzero(part["stratum"].to_numpy() == name) for name in part["stratum"].unique()]
        draws = []
        for _ in range(samples):
            drawn = np.concatenate([rng.choice(cell, size=len(cell), replace=True) for cell in strata])
            draws.append((w[drawn, None] * values[drawn]).sum(axis=0) / w[drawn].sum())
        bounds = np.quantile(np.array(draws), [alpha, 1 - alpha], axis=0) if draws else np.full((2, values.shape[1]), np.nan)
        for position, variable in enumerate(indicators.columns):
            rows.append({"platform": platform, "variable": variable, "share": point[position],
                         "low": bounds[0, position], "high": bounds[1, position],
                         "positives": int(values[:, position].sum()), "units": len(part)})
    return pd.DataFrame(rows)


def weighted_share_by_year(
    reference: pd.DataFrame, manifest: pd.DataFrame, platform: str, categories: Sequence[str],
    samples: int = BOOTSTRAP_SAMPLES, seed: int = SEED,
) -> pd.DataFrame:
    """Share of a platform's units whose source types include any of `categories`, per year and over all years.

    Weights and intervals as in `weighted_shares`: N_h over the labelled units of
    the stratum, bootstrap within strata. The year comes from the manifest; the row
    with `year` "all" covers every year.
    """
    design = manifest.loc[manifest["platform"].eq(platform), ["unit_id", "stratum", "N_h", "year"]].astype({"unit_id": str})
    frame = reference.loc[reference["platform"].eq(platform), ["unit_id", "source_types"]].astype({"unit_id": str}).merge(
        design, on="unit_id"
    ).reset_index(drop=True)
    w = (frame["N_h"] / frame.groupby("stratum")["unit_id"].transform("size")).to_numpy(float)
    hit = np.array([float(bool(labels & set(categories))) for labels in label_sets(frame["source_types"])])
    years = frame["year"].astype(int).to_numpy()
    groups = {**{int(year): years == year for year in np.unique(years)}, "all": np.ones(len(frame), dtype=bool)}

    def shares(rows: np.ndarray) -> dict:
        chosen = {key: rows[mask[rows]] for key, mask in groups.items()}
        return {key: float((w[part] * hit[part]).sum() / w[part].sum()) for key, part in chosen.items()}

    point = shares(np.arange(len(frame)))
    rng = np.random.default_rng(seed)
    strata = [np.flatnonzero(frame["stratum"].to_numpy() == name) for name in frame["stratum"].unique()]
    draws = [shares(np.concatenate([rng.choice(cell, size=len(cell), replace=True) for cell in strata])) for _ in range(samples)]
    alpha = (1 - CONFIDENCE) / 2
    return pd.DataFrame([
        {"year": key, "share": point[key],
         "low": float(np.quantile([draw[key] for draw in draws], alpha)) if draws else np.nan,
         "high": float(np.quantile([draw[key] for draw in draws], 1 - alpha)) if draws else np.nan,
         "positives": int(hit[mask].sum()), "units": int(mask.sum())}
        for key, mask in groups.items()
    ])


def _chi_square(groups: np.ndarray, errors: np.ndarray, levels: int) -> float:
    """Chi-square statistic of the groups x (error, no error) table, over cells with a positive expected count."""
    totals = np.bincount(groups, minlength=levels).astype(float)
    wrong = np.bincount(groups, weights=errors.astype(float), minlength=levels)
    observed = np.stack([wrong, totals - wrong])
    expected = np.outer([errors.sum(), len(errors) - errors.sum()], totals) / len(errors)
    keep = expected > 0
    return float((((observed - expected) ** 2)[keep] / expected[keep]).sum())


def differential_errors(
    frame: pd.DataFrame, group: str, variable: str = "cites_source",
    samples: int = BOOTSTRAP_SAMPLES, permutations: int = 2000, seed: int = SEED,
) -> pd.DataFrame:
    """Error rates of a binary variable per group: false positives among gold negatives, false negatives among gold positives.

    `frame` is `paired` output with a `group` column. Rates are weighted, with
    bootstrap intervals within strata. `p_permutation` tests whether the error
    counts differ between groups: the chi-square statistic of the unweighted
    groups x error table against permutations of the errors among the units.
    """
    rng = np.random.default_rng(seed)
    alpha = (1 - CONFIDENCE) / 2
    rows = []
    present = frame[frame[variable].notna() & frame[f"{variable}_pred"].notna()]
    for platform, part in present.groupby("platform"):
        y = part[variable].astype(int).to_numpy().astype(bool)
        p = part[f"{variable}_pred"].astype(int).to_numpy().astype(bool)
        for kind, among, wrong in [("false_positive_rate", ~y, p & ~y), ("false_negative_rate", y, ~p & y)]:
            subset = part[among].reset_index(drop=True)
            errors = wrong[among]
            names = subset[group].astype(str).to_numpy()
            levels = sorted(set(names))
            codes = np.array([levels.index(name) for name in names], dtype=int)
            p_value = np.nan
            if len(levels) > 1 and 0 < errors.sum() < len(errors):
                observed = _chi_square(codes, errors, len(levels))
                exceed = sum(_chi_square(codes, rng.permutation(errors), len(levels)) >= observed - 1e-12
                             for _ in range(permutations))
                p_value = (exceed + 1) / (permutations + 1)
            for name in levels:
                chosen = names == name
                cell, cell_errors = subset[chosen].reset_index(drop=True), errors[chosen]
                w = cell["weight"].to_numpy(float)
                rate = (w * cell_errors).sum() / w.sum() if w.sum() else np.nan
                strata = [np.flatnonzero(cell["stratum"].to_numpy() == stratum) for stratum in cell["stratum"].unique()]
                draws = []
                for _ in range(samples if len(cell) else 0):
                    drawn = np.concatenate([rng.choice(index, size=len(index), replace=True) for index in strata])
                    draws.append((w[drawn] * cell_errors[drawn]).sum() / w[drawn].sum())
                low, high = np.quantile(draws, [alpha, 1 - alpha]) if draws else (np.nan, np.nan)
                rows.append({"platform": platform, "variable": variable, "grouping": group, "group": name, "rate": kind,
                             "value": rate, "low": low, "high": high, "errors": int(cell_errors.sum()), "units": len(cell),
                             "p_permutation": p_value})
    return pd.DataFrame(rows)


def mcnemar(frame: pd.DataFrame, first: str, second: str, variable: str = "cites_source") -> dict:
    """Exact McNemar test of two instruments on the same gold units (`first` and `second` are prediction columns)."""
    from scipy.stats import binomtest

    present = frame[frame[variable].notna() & frame[first].notna() & frame[second].notna()]
    truth = present[variable].astype(int).to_numpy()
    right_first = present[first].astype(int).to_numpy() == truth
    right_second = present[second].astype(int).to_numpy() == truth
    only_first, only_second = int((right_first & ~right_second).sum()), int((~right_first & right_second).sum())
    discordant = only_first + only_second
    p_value = binomtest(min(only_first, only_second), discordant, 0.5).pvalue if discordant else 1.0
    return {"units": len(present), "only_first_right": only_first, "only_second_right": only_second,
            "both_right": int((right_first & right_second).sum()), "both_wrong": int((~right_first & ~right_second).sum()),
            "p_exact": float(p_value)}


def ranking_agreement(shares: pd.DataFrame, reference: str = "gold") -> pd.DataFrame:
    """Kendall's tau-b between each source's category ranking and that of `reference`, per platform.

    `shares` has the columns platform, source (gold or an instrument), variable
    (a category) and share.
    """
    from scipy.stats import kendalltau

    rows = []
    for platform, part in shares.groupby("platform"):
        table = part.pivot(index="variable", columns="source", values="share")
        if reference not in table:
            continue
        for source in table.columns.drop(reference):
            both = table[[reference, source]].dropna()
            tau, p_value = kendalltau(both[reference], both[source]) if len(both) > 1 else (np.nan, np.nan)
            rows.append({"platform": platform, "source": source, "reference": reference, "categories": len(both),
                         "kendall_tau": float(tau), "p_value": float(p_value),
                         "same_top_category": bool(len(both)) and both[reference].idxmax() == both[source].idxmax()})
    return pd.DataFrame(rows)
