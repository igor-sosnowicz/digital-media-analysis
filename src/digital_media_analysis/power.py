"""Power of the v2 trend tests by simulation (docs/hipotezy_v2.md): how many units the frames need.

Each replicate draws groups (subreddits or pages) with random intercepts on the
logit scale around the base rate, a yearly trend, and units per group and
year, then fits the preregistered model (logit with group fixed effects) and
records whether the one-sided trend test rejects at alpha (power) and whether
TOST shows equivalence when the true trend is zero (power to show no trend).
Wald errors without clustering keep the simulation fast; clustering by day or
revision widens the intervals, so the numbers are an upper bound.
"""

from collections.abc import Sequence

import numpy as np
import pandas as pd
from scipy.special import expit, logit
from scipy.stats import norm


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
             replicates: int = 200, seed: int = 20261025, fixed_effects: bool = True) -> dict:
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
