"""Inter-annotator agreement: Cohen's kappa and Krippendorff's alpha with bootstrap intervals.

Alpha is computed from value counts (Krippendorff 2011), so one implementation
handles nominal values and the set-valued `source_types` (MASI distance,
Passonneau 2006). Intervals are percentile bootstrap intervals over units
resampled with replacement.
"""

from collections.abc import Callable, Hashable, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

from digital_media_analysis.instruments.labels import LABEL_SEPARATOR

BOOTSTRAP_SAMPLES = 2000
CONFIDENCE = 0.95
SEED = 20261016
# Krippendorff (2004): alpha >= 0.8 is reliable; 0.667-0.8 allows tentative conclusions only.
ALPHA_RELIABLE = 0.8
ALPHA_TENTATIVE = 0.667
# Below this many units marked positive by any annotator, perfect agreement on a
# handful of cases says nothing; such rows are reported, but not judged.
MIN_POSITIVE_UNITS = 5

Distance = Callable[[Hashable, Hashable], float]


@dataclass(frozen=True)
class Estimate:
    value: float
    low: float = np.nan
    high: float = np.nan


def nominal_distance(first: Hashable, second: Hashable) -> float:
    return 0.0 if first == second else 1.0


def masi_distance(first: frozenset, second: frozenset) -> float:
    """1 - MASI: Jaccard similarity scaled by 1 (equal), 2/3 (subset), 1/3 (overlap) or 0."""
    if first == second:
        return 0.0
    if first <= second or second <= first:
        monotonicity = 2 / 3
    elif first & second:
        monotonicity = 1 / 3
    else:
        monotonicity = 0.0
    return 1.0 - len(first & second) / len(first | second) * monotonicity


def krippendorff_alpha(
    units: Sequence[Sequence],
    distance: Distance = nominal_distance,
    samples: int = BOOTSTRAP_SAMPLES,
    seed: int = SEED,
) -> Estimate:
    """Alpha for rows of values (one row per unit, one entry per annotator; None = missing)."""
    counts, observed, delta = _alpha_parts(units, distance)
    if not len(observed):
        return Estimate(np.nan)

    def statistic(weights: np.ndarray) -> np.ndarray:
        value_counts = weights @ counts
        pairable = value_counts.sum(axis=-1)
        expected = np.einsum("...v,vw,...w->...", value_counts, delta, value_counts)
        with np.errstate(divide="ignore", invalid="ignore"):
            alpha = 1 - (pairable - 1) * (weights @ observed) / expected
        return np.where(expected > 0, alpha, np.nan)

    return _estimate(statistic, len(observed), samples, seed)


def cohen_kappa(
    first: Sequence[Hashable],
    second: Sequence[Hashable],
    samples: int = BOOTSTRAP_SAMPLES,
    seed: int = SEED,
) -> Estimate:
    """Kappa for two annotators over the units both of them coded."""
    pairs = [(a, b) for a, b in zip(first, second) if not _missing(a) and not _missing(b)]
    if not pairs:
        return Estimate(np.nan)
    categories = sorted({value for pair in pairs for value in pair}, key=repr)
    index = {value: position for position, value in enumerate(categories)}
    size = len(categories)
    cells = np.zeros((len(pairs), size * size))
    for unit, (a, b) in enumerate(pairs):
        cells[unit, index[a] * size + index[b]] = 1

    def statistic(weights: np.ndarray) -> np.ndarray:
        table = (weights @ cells).reshape(*weights.shape[:-1], size, size)
        total = table.sum(axis=(-2, -1))
        observed = np.trace(table, axis1=-2, axis2=-1) / total
        expected = (table.sum(axis=-1) * table.sum(axis=-2)).sum(axis=-1) / total**2
        with np.errstate(divide="ignore", invalid="ignore"):
            kappa = (observed - expected) / (1 - expected)
        return np.where(expected < 1, kappa, np.nan)

    return _estimate(statistic, len(pairs), samples, seed)


def _missing(value: object) -> bool:
    if value is None or isinstance(value, frozenset):
        return value is None
    return bool(pd.isna(value))


def _alpha_parts(units: Sequence[Sequence], distance: Distance):
    """Per-unit value counts, per-unit observed disagreement and the distance matrix."""
    rows = [[value for value in unit if not _missing(value)] for unit in units]
    rows = [row for row in rows if len(row) >= 2]
    values = sorted({value for row in rows for value in row}, key=repr)
    index = {value: position for position, value in enumerate(values)}
    delta = np.array([[distance(a, b) for b in values] for a in values]).reshape(len(values), len(values))
    counts = np.zeros((len(rows), len(values)))
    observed = np.zeros(len(rows))
    for unit, row in enumerate(rows):
        positions = [index[value] for value in row]
        np.add.at(counts[unit], positions, 1)
        pair_sum = sum(delta[i, j] for a, i in enumerate(positions) for b, j in enumerate(positions) if a != b)
        observed[unit] = pair_sum / (len(row) - 1)
    return counts, observed, delta


def _estimate(statistic: Callable[[np.ndarray], np.ndarray], units: int, samples: int, seed: int) -> Estimate:
    value = float(statistic(np.ones(units)))
    if samples <= 0 or np.isnan(value):
        return Estimate(value)
    rng = np.random.default_rng(seed)
    weights = rng.multinomial(units, np.full(units, 1 / units), size=samples).astype(float)
    replicates = statistic(weights)
    replicates = replicates[np.isfinite(replicates)]
    if not len(replicates):
        return Estimate(value)
    tail = (1 - CONFIDENCE) / 2 * 100
    low, high = np.percentile(replicates, [tail, 100 - tail])
    return Estimate(value, float(low), float(high))


# --- Label tables ---------------------------------------------------------------


def variables_for(platform: str, category_codes: Sequence[str]) -> list[str]:
    """Variables to compare: binary codes, the whole label set, then one indicator per category."""
    binary = ["cites_source"] + (["edit_about_sources"] if platform == "wikipedia" else [])
    return binary + ["source_types"] + [f"source_types:{code}" for code in category_codes]


def coded_values(labels: pd.DataFrame, variable: str) -> pd.Series:
    """One comparable value per label row; None where the annotator gave no usable label."""
    if variable in {"cites_source", "edit_about_sources", "uncertain"}:
        return labels[variable].map(lambda value: None if pd.isna(value) else int(value))
    codes = labels["source_types"].fillna("").map(
        lambda text: frozenset(code for code in text.split(LABEL_SEPARATOR) if code)
    )
    if variable.startswith("source_types:"):
        category = variable.split(":", 1)[1]
        codes = codes.map(lambda label_set: int(category in label_set))
    elif variable != "source_types":
        raise ValueError(f"Unknown variable {variable!r}")
    return codes.where(labels["cites_source"].notna(), None)


def value_matrix(labels: pd.DataFrame, variable: str) -> pd.DataFrame:
    """Units x annotators table of coded values for one variable."""
    return labels.assign(value=coded_values(labels, variable)).pivot(
        index="unit_id", columns="annotator", values="value"
    )


def agreement_table(
    labels: pd.DataFrame,
    category_codes: Sequence[str],
    samples: int = BOOTSTRAP_SAMPLES,
    seed: int = SEED,
) -> pd.DataFrame:
    """Agreement per platform and variable: observed agreement, prevalence, kappa and alpha."""
    rows = []
    for platform, platform_labels in labels.groupby("platform"):
        annotators = sorted(platform_labels["annotator"].unique())
        for variable in variables_for(platform, category_codes):
            matrix = value_matrix(platform_labels, variable)
            units = [[value for value in row if not _missing(value)] for row in matrix.itertuples(index=False)]
            units = [row for row in units if len(row) >= 2]
            set_valued = variable == "source_types"
            values = [value for row in units for value in row]
            positive_units = sum(any(_positive(value) for value in row) for row in units)
            kappa = (
                cohen_kappa(matrix[annotators[0]].tolist(), matrix[annotators[1]].tolist(), samples, seed)
                if len(annotators) == 2 and not set_valued
                else Estimate(np.nan)
            )
            alpha = krippendorff_alpha(units, masi_distance if set_valued else nominal_distance, samples, seed)
            rows.append({
                "platform": platform,
                "variable": variable,
                "units": len(units),
                "annotators": len(annotators),
                "positive_units": positive_units,
                "observed_agreement": np.mean([len(set(row)) == 1 for row in units]) if units else np.nan,
                "prevalence": np.nan if set_valued or not values else float(np.mean(values)),
                "kappa": kappa.value,
                "kappa_low": kappa.low,
                "kappa_high": kappa.high,
                "alpha": alpha.value,
                "alpha_low": alpha.low,
                "alpha_high": alpha.high,
                "distance": "MASI" if set_valued else "nominal",
                "verdict": verdict(alpha, positive_units),
            })
    return pd.DataFrame(rows)


def verdict(alpha: Estimate, positive_units: int | None = None) -> str:
    """Reading of alpha against Krippendorff's thresholds, using the lower interval bound when known."""
    if positive_units is not None and positive_units < MIN_POSITIVE_UNITS:
        return "za mało przypadków"
    if np.isnan(alpha.value):
        return "brak zmienności"
    bound = alpha.value if np.isnan(alpha.low) else alpha.low
    if bound >= ALPHA_RELIABLE:
        return "rzetelne"
    if alpha.value >= ALPHA_RELIABLE:
        return "rzetelne punktowo, przedział niepewny"
    if alpha.value >= ALPHA_TENTATIVE:
        return "tylko wstępne wnioski"
    return "niewystarczające"


def disagreements(labels: pd.DataFrame) -> pd.DataFrame:
    """Units where annotators differ on `cites_source`, `source_types` or `edit_about_sources`."""
    rows = []
    for platform, platform_labels in labels.groupby("platform"):
        variables = ["cites_source", "source_types"] + (["edit_about_sources"] if platform == "wikipedia" else [])
        uncertain = platform_labels.pivot(index="unit_id", columns="annotator", values="uncertain")
        for variable in variables:
            matrix = value_matrix(platform_labels, variable)
            for unit_id, row in matrix.iterrows():
                present = [value for value in row if not _missing(value)]
                if len(present) >= 2 and len(set(present)) > 1:
                    rows.append({
                        "unit_id": unit_id,
                        "platform": platform,
                        "variable": variable,
                        **{annotator: _display(value) for annotator, value in row.items()},
                        "uncertain": ", ".join(
                            annotator for annotator, flag in uncertain.loc[unit_id].items()
                            if not pd.isna(flag) and flag == 1
                        ),
                    })
    return pd.DataFrame(rows)


def _positive(value: object) -> bool:
    """A non-empty label set or a 1 on a binary variable."""
    return len(value) > 0 if isinstance(value, frozenset) else value == 1


def _display(value: object) -> str:
    if isinstance(value, frozenset):
        return LABEL_SEPARATOR.join(sorted(value)) or "(brak)"
    return "" if _missing(value) else str(value)


def annotator_summary(labels: pd.DataFrame) -> pd.DataFrame:
    """Per annotator: units coded, share citing a source, mean label-set size, share uncertain."""
    sizes = coded_values(labels, "source_types").map(lambda label_set: np.nan if label_set is None else len(label_set))
    return (
        labels.assign(set_size=sizes.where(labels["cites_source"].eq(1).fillna(False)))
        .groupby(["platform", "annotator"])
        .agg(
            units=("unit_id", "size"),
            cites_share=("cites_source", "mean"),
            mean_types_when_citing=("set_size", "mean"),
            uncertain_share=("uncertain", "mean"),
        )
    )


# --- Plot -----------------------------------------------------------------------

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
GRID = "#e4e3df"
SERIES = "#2a78d6"
VARIABLE_LABELS = {
    "cites_source": "powołanie się na źródło",
    "edit_about_sources": "edycja dotyczy źródeł",
    "source_types": "typy źródeł (cały zbiór, MASI)",
}


def plot_alpha(table: pd.DataFrame, path=None):
    """Dot-and-interval plot of alpha per variable, one panel per platform."""
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter

    platforms = list(dict.fromkeys(table["platform"]))
    rows_per_panel = max(table["platform"].value_counts())
    figure, axes = plt.subplots(
        1, len(platforms), figsize=(6.2 * len(platforms), 0.36 * rows_per_panel + 1.6),
        squeeze=False, facecolor=SURFACE,
    )
    finite_lows = table["alpha_low"].dropna()
    left = max(-1.0, min(-0.25, (finite_lows.min() if len(finite_lows) else 0) - 0.05))
    for axis, platform in zip(axes[0], platforms):
        rows = table[table["platform"].eq(platform)].reset_index(drop=True)
        positions = np.arange(len(rows))[::-1]
        axis.set_facecolor(SURFACE)
        axis.set_xlim(left, 1.02)
        axis.set_ylim(-0.7, len(rows) - 0.1)
        for threshold, label, alignment in [
            (ALPHA_TENTATIVE, f"{ALPHA_TENTATIVE:.3f}: wnioski wstępne ", "right"),
            (ALPHA_RELIABLE, f" {ALPHA_RELIABLE:.1f}: rzetelne", "left"),
        ]:
            axis.axvline(threshold, color=INK_SECONDARY, linewidth=1, linestyle=(0, (4, 3)), zorder=1)
            axis.text(threshold, len(rows) - 0.35, label.replace(".", ","), ha=alignment, va="bottom",
                      fontsize=8, color=INK_SECONDARY)
        for position, row in zip(positions, rows.itertuples(index=False)):
            if row.positive_units < MIN_POSITIVE_UNITS or np.isnan(row.alpha):
                note = (f"za mało przypadków (k = {row.positive_units})"
                        if row.positive_units < MIN_POSITIVE_UNITS else "brak zmienności")
                axis.text(left + 0.03, position, note, va="center", ha="left", fontsize=8,
                          color=INK_SECONDARY, style="italic")
                continue
            if not np.isnan(row.alpha_low):
                axis.plot([max(row.alpha_low, left), row.alpha_high], [position, position],
                          color=SERIES, linewidth=2, solid_capstyle="round", zorder=2)
            axis.plot(row.alpha, position, "o", markersize=7, color=SERIES,
                      markeredgecolor=SURFACE, markeredgewidth=2, zorder=3)
            if not row.variable.startswith("source_types:"):
                axis.text(min(row.alpha_high if not np.isnan(row.alpha_high) else row.alpha, 1.0) + 0.02, position,
                          f"{row.alpha:.2f}".replace(".", ","), va="center", fontsize=8, color=INK)
        axis.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:.1f}".replace(".", ",").replace("-", "−")))
        axis.set_yticks(positions)
        axis.set_yticklabels(
            [VARIABLE_LABELS.get(variable, variable.replace("source_types:", "typ: ")) for variable in rows["variable"]],
            fontsize=9, color=INK,
        )
        overall = rows["variable"].str.startswith("source_types:").idxmax()
        axis.axhline(positions[overall] + 0.5, color=GRID, linewidth=1)
        axis.grid(axis="x", color=GRID, linewidth=0.8)
        axis.set_axisbelow(True)
        axis.tick_params(colors=INK_SECONDARY, length=0)
        for side in ["top", "right", "left"]:
            axis.spines[side].set_visible(False)
        axis.spines["bottom"].set_color(GRID)
        units = int(rows.loc[rows["variable"].eq("cites_source"), "units"].iloc[0])
        axis.set_title(f"{platform.capitalize()} (n = {units})", loc="left", fontsize=11, color=INK)
        axis.set_xlabel("α Krippendorffa z 95% przedziałem bootstrap", fontsize=9, color=INK_SECONDARY)
    figure.tight_layout()
    if path is not None:
        figure.savefig(path, dpi=200, facecolor=SURFACE)
    return figure
