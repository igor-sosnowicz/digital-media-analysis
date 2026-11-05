"""Power of the v2 trend tests by simulation (docs/hipotezy_v2.md): how many units the frames need.

Each replicate draws groups (subreddits or pages) with random intercepts on the
logit scale around the base rate, a yearly trend, and units per group and
year, then fits the preregistered model (logit with group fixed effects) and
records whether the one-sided trend test rejects at alpha (power) and whether
TOST shows equivalence when the true trend is zero (power to show no trend).
Wald errors without clustering keep the simulation fast; clustering by day or
revision widens the intervals, so the numbers are an upper bound. A simulated
instrument (sensitivity, specificity) can stand between the true and the coded
outcome.

The planning formulas (docs/plan_poprawy_krok_po_kroku.md, section 1.2) give the
same power analytically, with instrument error and a design effect: the
instrument sees the share p as p_obs = Se p + (1 - Sp)(1 - p) and flattens the
trend by (Se + Sp - 1) p(1 - p) / (p_obs (1 - p_obs)), and clustering divides the
information by the design effect. Equivalence power assumes the bound is applied
on the corrected scale, so it shrinks with the same factor.
"""

from collections.abc import Sequence

import numpy as np
import pandas as pd
from scipy.special import expit, logit
from scipy.stats import binom, norm


def _fit_trend(year: np.ndarray, group: np.ndarray, y: np.ndarray, fixed_effects: bool = True) -> tuple[float, float]:
    """Year coefficient and its Wald standard error of a logit with group fixed effects (or pooled), by Newton iterations."""
    groups = np.unique(group)
    dummies = (group[:, None] == groups[None, 1:]).astype(float) if fixed_effects else np.empty((len(y), 0))
    x = np.column_stack([np.ones(len(y)), year, dummies])
    beta = np.zeros(x.shape[1])
    beta[0] = logit(np.clip(y.mean(), 1e-4, 1 - 1e-4))
    for _ in range(50):
        p = expit(x @ beta)
        w = p * (1 - p) + 1e-9
        information = (x * w[:, None]).T @ x
        step = np.linalg.solve(information + 1e-8 * np.eye(len(beta)), x.T @ (y - p))
        beta += step
        if np.max(np.abs(step)) < 1e-8:
            break
    p = expit(x @ beta)
    covariance = np.linalg.pinv((x * (p * (1 - p))[:, None]).T @ x)
    return float(beta[1]), float(np.sqrt(covariance[1, 1]))


def simulate(groups: int, years: int, per_cell: int, base_rate: float, odds_ratio_per_year: float,
             intercept_sd: float = 0.5, alpha: float = 0.05, equivalence_odds_ratio: float | None = None,
             replicates: int = 200, seed: int = 20261025, fixed_effects: bool = True,
             sensitivity: float = 1.0, specificity: float = 1.0) -> dict:
    """Share of replicates in which the one-sided test rejects (and TOST shows equivalence, if a bound is given)."""
    rng = np.random.default_rng(seed)
    year = np.tile(np.repeat(np.arange(years, dtype=float), per_cell), groups)
    group = np.repeat(np.arange(groups), years * per_cell)
    rejects, equivalent = 0, 0
    z = norm.ppf(1 - alpha)
    for _ in range(replicates):
        intercepts = logit(base_rate) + rng.normal(0, intercept_sd, groups)
        p = expit(intercepts[group] + np.log(odds_ratio_per_year) * (year - (years - 1) / 2))
        y = (rng.random(len(p)) < p).astype(float)
        if sensitivity < 1 or specificity < 1:  # extra draws only then, so the error-free results stay as before
            noise = rng.random(len(y))
            y = np.where(y == 1, noise < sensitivity, noise < 1 - specificity).astype(float)
        if y.sum() == 0 or y.sum() == len(y):
            continue
        beta, se = _fit_trend(year, group, y, fixed_effects)
        direction = 1 if odds_ratio_per_year >= 1 else -1
        rejects += direction * beta / se > z
        if equivalence_odds_ratio:
            delta = np.log(equivalence_odds_ratio)
            equivalent += (beta + delta) / se > z and (beta - delta) / se < -z
    return {"groups": groups, "years": years, "per_cell": per_cell, "units": groups * years * per_cell,
            "base_rate": base_rate, "odds_ratio_per_year": odds_ratio_per_year, "power": rejects / replicates,
            "power_equivalence": equivalent / replicates if equivalence_odds_ratio else np.nan}


def curve(groups: int, years: int, per_cells: Sequence[int], base_rate: float, odds_ratio_per_year: float,
          equivalence_odds_ratio: float, replicates: int = 200, seed: int = 20261025, fixed_effects: bool = True) -> pd.DataFrame:
    """Power to detect the trend, and to show equivalence under no trend, for each units-per-cell value."""
    rows = []
    for per_cell in per_cells:
        effect = simulate(groups, years, per_cell, base_rate, odds_ratio_per_year, replicates=replicates, seed=seed,
                          fixed_effects=fixed_effects)
        null = simulate(groups, years, per_cell, base_rate, 1.0, equivalence_odds_ratio=equivalence_odds_ratio,
                        replicates=replicates, seed=seed + 1, fixed_effects=fixed_effects)
        rows.append({**effect, "power_equivalence": null["power_equivalence"], "false_positive_rate": null["power"]})
    return pd.DataFrame(rows)


# --- Planning formulas (docs/plan_poprawy_krok_po_kroku.md, section 1.2) -----------------------------------------


def year_variance(years: int) -> float:
    """Variance of the year when every one of `years` consecutive years has the same number of units."""
    return (years**2 - 1) / 12


def observed_share(share: float, sensitivity: float = 1.0, specificity: float = 1.0) -> float:
    """Share an instrument with this sensitivity and specificity reports when the true share is `share`."""
    return sensitivity * share + (1 - specificity) * (1 - share)


def trend_z(units: float, share: float, log_odds_per_year: float, years: int, sensitivity: float = 1.0,
            specificity: float = 1.0, design_effect: float = 1.0) -> float:
    """Expected z of the logit trend test for a true trend, seen through the instrument, with a design effect."""
    seen = observed_share(share, sensitivity, specificity)
    slope = (sensitivity + specificity - 1) * log_odds_per_year * share * (1 - share) / (seen * (1 - seen))
    return float(slope * np.sqrt(units * seen * (1 - seen) * year_variance(years) / design_effect))


def trend_power(units: float, share: float, log_odds_per_year: float, years: int, sensitivity: float = 1.0,
                specificity: float = 1.0, design_effect: float = 1.0, alpha: float = 0.05) -> float:
    """Power of the one-sided trend test when the true trend is `log_odds_per_year`."""
    z = trend_z(units, share, log_odds_per_year, years, sensitivity, specificity, design_effect)
    return float(norm.cdf(z - norm.ppf(1 - alpha)))


def equivalence_power(units: float, share: float, bound_log_odds_per_year: float, years: int, sensitivity: float = 1.0,
                      specificity: float = 1.0, design_effect: float = 1.0, alpha: float = 0.05) -> float:
    """Power of TOST against the bound when there is no trend (bound on the corrected scale)."""
    z = trend_z(units, share, bound_log_odds_per_year, years, sensitivity, specificity, design_effect)
    return float(max(0.0, 2 * norm.cdf(z - norm.ppf(1 - alpha)) - 1))


def units_needed(share: float, log_odds_per_year: float, years: int, sensitivity: float = 1.0, specificity: float = 1.0,
                 design_effect: float = 1.0, target: float = 0.8, alpha: float = 0.05, equivalence: bool = False) -> int:
    """Units for the target power of the trend test (or, with `equivalence`, of TOST under no trend)."""
    per_unit = trend_z(1, share, log_odds_per_year, years, sensitivity, specificity, design_effect)
    needed = norm.ppf(1 - alpha) + (norm.ppf((1 + target) / 2) if equivalence else norm.ppf(target))
    return int(np.ceil((needed / per_unit) ** 2))


def two_share_power(first: float, second: float, units_first: float, units_second: float, design_effect: float = 1.0,
                    alpha: float = 0.05) -> float:
    """Power of the one-sided test that two shares differ in the expected direction (normal approximation)."""
    error = np.sqrt(design_effect * (first * (1 - first) / units_first + second * (1 - second) / units_second))
    return float(norm.cdf(abs(first - second) / error - norm.ppf(1 - alpha)))


def bound_power(units: float, share: float, bound: float, design_effect: float = 1.0, alpha: float = 0.05) -> float:
    """Power of the one-sided test that a share lies below `bound` when it truly is `share`."""
    error = np.sqrt(design_effect * share * (1 - share) / units)
    return float(norm.cdf((bound - share) / error - norm.ppf(1 - alpha)))


def events_needed(exposed_share: float, hazard_ratio: float, target: float = 0.8, alpha: float = 0.05) -> int:
    """Events (removals) a one-sided Cox test needs to detect the hazard ratio (Schoenfeld 1983)."""
    needed = (norm.ppf(1 - alpha) + norm.ppf(target)) ** 2
    return int(np.ceil(needed / (exposed_share * (1 - exposed_share) * np.log(hazard_ratio) ** 2)))


def binomial_power(units: int, share: float, null_share: float, alpha: float = 0.05) -> float:
    """Exact power of the one-sided binomial test that the share exceeds `null_share`."""
    critical = int(binom.isf(alpha, units, null_share)) + 1  # smallest count with P(X >= count | null) <= alpha
    return float(binom.sf(critical - 1, units, share))


def design_effect(values: Sequence[float], clusters: Sequence[object]) -> dict:
    """Design effect of clustered binary or numeric values: 1 + (m - 1) ICC, with the size-weighted mean cluster size m
    and the ANOVA estimate of the intraclass correlation (negative estimates kept, so the effect can fall below 1)."""
    frame = pd.DataFrame({"y": np.asarray(values, dtype=float), "cluster": np.asarray(clusters)})
    groups = frame.groupby("cluster")["y"]
    sizes, units = groups.size(), len(frame)
    if len(sizes) < 2 or units == len(sizes):
        return {"units": units, "clusters": len(sizes), "icc": np.nan, "mean_size": float(sizes.mean()), "design_effect": 1.0}
    n0 = (units - (sizes**2).sum() / units) / (len(sizes) - 1)
    between = (sizes * (groups.mean() - frame["y"].mean()) ** 2).sum() / (len(sizes) - 1)
    within = ((frame["y"] - groups.transform("mean")) ** 2).sum() / (units - len(sizes))
    icc = (between - within) / (between + (n0 - 1) * within) if between + (n0 - 1) * within > 0 else 0.0
    weighted_size = float((sizes**2).sum() / units)
    return {"units": units, "clusters": len(sizes), "icc": float(icc), "mean_size": weighted_size,
            "design_effect": float(1 + (weighted_size - 1) * icc)}
