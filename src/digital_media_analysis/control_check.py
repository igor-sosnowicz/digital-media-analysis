"""Variant A done automatically (amendment of 27.10.2026): control samples for a blind second coding by the AI assistant.

Three samples, drawn once with SEED before any coding:
- stance: rows people were to decide (`decided_by = human`) in the four stance sheets; every row labelled
  `challenges` in the test half (certain stratum), the rest a simple random sample up to STANCE_SIZE rows;
- audit: AUDIT_SIZE random rows of the audit sheet people were to decide;
- sources: SOURCES_SIZE Reddit posts of the source pilot that IS and JP coded independently with identical `source_types`.

The blind files hold only the post text, in random order. Scores compare the blind labels with the sheet labels
(stance, audit: stability of the AI labels) and with the human consensus (sources: AI error against people).
"""

import math
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20261027
STANCE_SIZE = 84
AUDIT_SIZE = 30
SOURCES_SIZE = 30
TEXT_COLUMNS = ["unit_id", "subreddit", "title", "text", "link"]
CERTAIN = "test_challenges"


def sheet_rows(path: Path, label: str, sheet: str = "Reddit") -> pd.DataFrame:
    """Rows of a review sheet: text columns (by position, the headers are Polish), the final label and who decides."""
    frame = pd.read_excel(path, sheet_name=sheet, dtype=str)
    text = frame.iloc[:, :5].set_axis(TEXT_COLUMNS, axis=1)
    return text.assign(label=frame[label].fillna("").str.strip(),
                       decided_by=frame.get("decided_by", pd.Series("", index=frame.index)).fillna(""),
                       sheet=path.name)


def draw_certain(rows: pd.DataFrame, certain: pd.Series, name: str, size: int, seed: int = SEED,
                 rest_name: str = "rest") -> pd.DataFrame:
    """Every row of the certain stratum plus a simple random sample of the other rows up to size, weights N_h / n_h."""
    rest = rows[~certain]
    chosen_rest = rest.sample(n=min(len(rest), max(size - int(certain.sum()), 0)), random_state=seed)
    parts = [rows[certain].assign(stratum=name, N_h=int(certain.sum()), n_h=int(certain.sum())),
             chosen_rest.assign(stratum=rest_name, N_h=len(rest), n_h=len(chosen_rest))]
    return pd.concat(parts, ignore_index=True).assign(weight=lambda d: d["N_h"] / d["n_h"])


def draw_stance(rows: pd.DataFrame, size: int = STANCE_SIZE, seed: int = SEED) -> pd.DataFrame:
    """All `challenges` rows of the test half plus a simple random sample of the other rows people were to decide."""
    rows = rows[rows["decided_by"].eq("human")]
    return draw_certain(rows, rows["split"].eq("test") & rows["label"].eq("challenges"), CERTAIN, size, seed)


def draw_sources(consensus: pd.DataFrame, single: pd.DataFrame, size: int = SOURCES_SIZE, seed: int = SEED) -> pd.DataFrame:
    """All pilot posts two people coded alike, filled up to size with gold posts one person coded (before AI help)."""
    single = single[~single["unit_id"].isin(consensus["unit_id"])]
    rows = pd.concat([consensus.assign(origin="pilot_consensus"), single.assign(origin="gold_single")], ignore_index=True)
    return draw_certain(rows, rows["origin"].eq("pilot_consensus"), "pilot_consensus", size, seed, rest_name="gold_single")


def draw_simple(rows: pd.DataFrame, size: int, seed: int = SEED, human_only: bool = True) -> pd.DataFrame:
    """A simple random sample (of the rows people were to decide, unless human_only is False)."""
    if human_only:
        rows = rows[rows["decided_by"].eq("human")]
    chosen = rows.sample(n=min(size, len(rows)), random_state=seed)
    return chosen.assign(stratum="all", N_h=len(rows), n_h=len(chosen), weight=len(rows) / len(chosen))


def label_set(value) -> frozenset:
    """`source_types` cell as a set of codes."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return frozenset()
    return frozenset(code.strip() for code in str(value).split(";") if code.strip())


def human_consensus(first: pd.DataFrame, second: pd.DataFrame) -> pd.DataFrame:
    """Reddit units both people coded with the same `source_types`, with that label."""
    columns = ["unit_id", "source_types"]
    pair = first.loc[first["platform"].eq("reddit"), columns].merge(
        second.loc[second["platform"].eq("reddit"), columns], on="unit_id", suffixes=("_1", "_2"))
    same = [bool(label_set(a)) and label_set(a) == label_set(b) for a, b in zip(pair["source_types_1"], pair["source_types_2"])]
    return pair[same].rename(columns={"source_types_1": "label"})[["unit_id", "label"]]


def blind(sample: pd.DataFrame, task: str, seed: int = SEED) -> pd.DataFrame:
    """Text only, in random order, so neither labels nor strata show."""
    return sample.sample(frac=1, random_state=seed)[TEXT_COLUMNS].assign(task=task)[["task", *TEXT_COLUMNS]]


def cohen_kappa(first: pd.Series, second: pd.Series) -> float:
    """Cohen's kappa of two nominal codings of the same units."""
    first, second = first.astype(str).reset_index(drop=True), second.astype(str).reset_index(drop=True)
    observed = float((first == second).mean())
    categories = set(first) | set(second)
    expected = sum(float((first == c).mean()) * float((second == c).mean()) for c in categories)
    return float("nan") if expected == 1 else (observed - expected) / (1 - expected)


def wilson(successes: float, total: float, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a proportion."""
    if total == 0:
        return float("nan"), float("nan")
    share = successes / total
    centre = (share + z * z / (2 * total)) / (1 + z * z / total)
    half = z * math.sqrt(share * (1 - share) / total + z * z / (4 * total * total)) / (1 + z * z / total)
    return centre - half, centre + half


def _row(task: str, measure: str, value: float, n: int, low: float = float("nan"), high: float = float("nan")) -> dict:
    return {"task": task, "measure": measure, "value": value, "low": low, "high": high, "n": n}


def score_stance(frame: pd.DataFrame) -> list[dict]:
    """Stability of the stance labels: frame has `label` (sheet), `blind` and `weight`."""
    same = frame["label"].eq(frame["blind"])
    weighted = float((same * frame["weight"]).sum() / frame["weight"].sum())
    rows = [_row("stance", "agreement", float(same.mean()), len(frame), *wilson(same.sum(), len(frame))),
            _row("stance", "agreement_weighted", weighted, len(frame)),
            _row("stance", "kappa", cohen_kappa(frame["label"], frame["blind"]), len(frame))]
    for stratum, part in frame.groupby("stratum"):
        hits = part["label"].eq(part["blind"])
        rows.append(_row("stance", f"agreement_{stratum}", float(hits.mean()), len(part), *wilson(hits.sum(), len(part))))
    sheet_challenges = frame["label"].eq("challenges")
    blind_challenges = frame["blind"].eq("challenges")
    kept = int((sheet_challenges & blind_challenges).sum())
    rows.append(_row("stance", "challenges_kept", kept / max(int(sheet_challenges.sum()), 1), int(sheet_challenges.sum()),
                     *wilson(kept, int(sheet_challenges.sum()))))
    rows.append(_row("stance", "challenges_confirmed", kept / max(int(blind_challenges.sum()), 1), int(blind_challenges.sum()),
                     *wilson(kept, int(blind_challenges.sum()))))
    return rows


def score_sets(frame: pd.DataFrame, task: str) -> list[dict]:
    """Agreement of two multilabel codings (`label`, `blind`): exact set, mean Jaccard, cites_source, each category."""
    first = [label_set(value) for value in frame["label"]]
    second = [label_set(value) for value in frame["blind"]]
    n = len(frame)
    exact = sum(a == b for a, b in zip(first, second))
    jaccard = [len(a & b) / len(a | b) if a | b else 1.0 for a, b in zip(first, second)]
    cites = sum((a != {"none"}) == (b != {"none"}) for a, b in zip(first, second))
    rows = [_row(task, "exact_set", exact / n, n, *wilson(exact, n)),
            _row(task, "jaccard_mean", float(np.mean(jaccard)), n),
            _row(task, "cites_source_agreement", cites / n, n, *wilson(cites, n))]
    if frame.get("stratum", pd.Series("all")).nunique() > 1:
        hits = pd.Series([a == b for a, b in zip(first, second)], index=frame.index)
        for stratum, part in hits.groupby(frame["stratum"]):
            rows.append(_row(task, f"exact_set_{stratum}", float(part.mean()), len(part), *wilson(part.sum(), len(part))))
    for code in sorted(set().union(*first, *second)):
        a = pd.Series([code in labels for labels in first])
        b = pd.Series([code in labels for labels in second])
        rows.append(_row(task, f"kappa_{code}", cohen_kappa(a, b), int((a | b).sum())))
    return rows


def disagreements(frame: pd.DataFrame, task: str, multilabel: bool) -> pd.DataFrame:
    """Units whose blind label differs from the reference (labels only, no text)."""
    if multilabel:
        differs = [label_set(a) != label_set(b) for a, b in zip(frame["label"], frame["blind"])]
    else:
        differs = frame["label"].ne(frame["blind"]).tolist()
    return frame.loc[differs, ["unit_id", "label", "blind"]].rename(columns={"label": "reference"}).assign(task=task)
