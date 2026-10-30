"""Exploratory robustness analyses of the hypothesis tests (not preregistered; docs/wyniki_hipotez.md).

Kept apart from the preregistered `hypotheses` module, so the confirmatory code
stays as committed. Firth's penalised logistic regression handles rare events
and separation: it maximises the log-likelihood plus half the log-determinant
of the Fisher information (Jeffreys prior), which keeps estimates finite and
reduces their small-sample bias, so fixed-effect levels without any event can
stay in the model. Its test and its 95% interval both come from the profile
penalised likelihood (Heinze and Schemper 2002), so they always agree.
"""

from collections.abc import Callable, Sequence
from itertools import combinations

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import chi2

# Critical value of the profile penalised likelihood-ratio statistic for a 95% interval.
CRITICAL = float(chi2.ppf(0.95, 1))


def _penalised_loglik(x: np.ndarray, y: np.ndarray, beta: np.ndarray) -> float:
    eta = x @ beta
    loglik = float(np.sum(y * eta - np.logaddexp(0, eta)))
    p = 1 / (1 + np.exp(-eta))
    information = (x * (p * (1 - p))[:, None]).T @ x
    sign, logdet = np.linalg.slogdet(information)
    return loglik + 0.5 * logdet if sign > 0 else -np.inf


def firth_logit(
    x: np.ndarray, y: np.ndarray, max_iter: int = 200, tol: float = 1e-8,
    fixed: dict[int, float] | None = None, start: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Coefficients, their covariance (inverse information) and the penalised log-likelihood of Firth's logit.

    `fixed` holds some coefficients at given values (column -> value) and fits the
    others; the penalty still uses the information of the whole design, as the
    profile penalised likelihood does. `start` gives the starting coefficients.
    """
    fixed = fixed or {}
    free = np.array([column for column in range(x.shape[1]) if column not in fixed], dtype=int)
    beta = np.zeros(x.shape[1]) if start is None else np.array(start, dtype=float)
    for column, value in fixed.items():
        beta[column] = value
    current = _penalised_loglik(x, y, beta)
    for _ in range(max_iter):
        p = 1 / (1 + np.exp(-(x @ beta)))
        w = p * (1 - p)
        information = (x * w[:, None]).T @ x
        leverage = w * np.einsum("ij,jk,ik->i", x, np.linalg.pinv(information), x)
        score = x.T @ (y - p + leverage * (0.5 - p))
        step = np.zeros_like(beta)
        step[free] = np.linalg.pinv(information[np.ix_(free, free)]) @ score[free]
        # Halve the step until the penalised likelihood does not fall.
        for _ in range(30):
            candidate = beta + step
            value = _penalised_loglik(x, y, candidate)
            if value >= current - 1e-12:
                break
            step = step / 2
        beta, current = candidate, value
        if np.max(np.abs(step)) < tol:
            break
    p = 1 / (1 + np.exp(-(x @ beta)))
    covariance = np.linalg.pinv((x * (p * (1 - p))[:, None]).T @ x)
    return beta, covariance, current


def design_matrix(frame: pd.DataFrame, fixed_effect: str | None, start_year: int) -> pd.DataFrame:
    columns = {"const": np.ones(len(frame)), "year": frame["year"].astype(float).to_numpy() - start_year}
    design = pd.DataFrame(columns, index=frame.index)
    if fixed_effect:
        design = pd.concat([design, pd.get_dummies(frame[fixed_effect], prefix="fe", drop_first=True, dtype=float)], axis=1)
    return design


def firth_trend(frame: pd.DataFrame, outcome: str, fixed_effect: str | None, direction: str, start_year: int) -> dict:
    """Year coefficient of Firth's logit with fixed effects (all levels kept), tested one-sided by penalised LR.

    The test and the 95% interval come from the same profile penalised likelihood:
    the year coefficient is held at a value and the others are refitted under the
    penalty of the whole design. The interval is the set of values the two-sided
    test does not reject, so it excludes no change exactly when that test rejects it.
    """
    y = frame[outcome].to_numpy(float)
    design = design_matrix(frame, fixed_effect, start_year)
    x = design.to_numpy()
    column = list(design.columns).index("year")
    beta, covariance, loglik = firth_logit(x, y)
    estimate, se = float(beta[column]), float(np.sqrt(covariance[column, column]))

    def deviance(value: float) -> float:
        start = beta.copy()
        start[column] = value
        return max(2 * (loglik - firth_logit(x, y, fixed={column: value}, start=start)[2]), 0.0)

    statistic = deviance(0.0)
    two_sided = float(chi2.sf(statistic, 1))
    toward = estimate > 0 if direction == "increase" else estimate < 0
    low, high = (_profile_bound(deviance, estimate, se, side) for side in (-1, 1))
    return {
        "beta": estimate, "se": se, "odds_ratio_per_year": float(np.exp(estimate)),
        "ci_low": float(np.exp(low)), "ci_high": float(np.exp(high)),
        "p_one_sided": two_sided / 2 if toward else 1 - two_sided / 2,
        "units": len(frame), "positives": int(y.sum()), "lr_statistic": statistic,
    }


def _profile_bound(deviance: Callable[[float], float], estimate: float, se: float, side: int) -> float:
    """Where the profile deviance reaches the 95% critical value below (side -1) or above (side 1) the estimate."""
    step = max(se, 1e-3)
    inner, outer = estimate, estimate + side * step
    for _ in range(40):
        if deviance(outer) >= CRITICAL:
            return float(brentq(lambda value: deviance(value) - CRITICAL, min(inner, outer), max(inner, outer), xtol=1e-6))
        inner, outer, step = outer, outer + side * step, 2 * step
    return side * np.inf


def revision_counts(links: pd.DataFrame, outcome: str) -> pd.DataFrame:
    """One row per revision that added links: page, year, links added, outcome links and whether there was any."""
    grouped = links.groupby(["page", "revision", "year"], as_index=False).agg(links=(outcome, "size"), events=(outcome, "sum"))
    return grouped.assign(any_event=grouped["events"].gt(0).astype(int))


def poisson_trend(revisions: pd.DataFrame, fixed_effect: str | None, direction: str, start_year: int) -> dict:
    """Year coefficient of a Poisson model of outcome links per revision, offset by the links it added (robust errors)."""
    import statsmodels.api as sm
    from scipy.stats import norm

    design = design_matrix(revisions, fixed_effect, start_year)
    varying = revisions.groupby(fixed_effect)["events"].transform("sum").gt(0) if fixed_effect else pd.Series(True, index=revisions.index)
    data, design = revisions[varying], design[varying]
    design = design.loc[:, design.abs().sum().gt(0)]
    fit = sm.GLM(data["events"], design, family=sm.families.Poisson(), offset=np.log(data["links"])).fit(cov_type="HC1")
    estimate, se = float(fit.params["year"]), float(fit.bse["year"])
    z = estimate / se
    return {
        "beta": estimate, "se": se, "rate_ratio_per_year": float(np.exp(estimate)),
        "ci_low": float(np.exp(estimate - 1.96 * se)), "ci_high": float(np.exp(estimate + 1.96 * se)),
        "p_one_sided": float(norm.sf(z) if direction == "increase" else norm.cdf(z)),
        "units": len(data), "positives": int(data["events"].sum()),
    }


def leave_one_out(frame: pd.DataFrame, outcome: str, fit, ids: Sequence) -> pd.DataFrame:
    """Refit after dropping each event row in turn; `fit(frame)` returns a result dict."""
    rows = []
    for index in ids:
        result = fit(frame.drop(index=index))
        rows.append({"dropped": index, **result})
    return pd.DataFrame(rows)


def exact_year_sum_test(years: Sequence[int], observed: Sequence[int]) -> float:
    """Exact conditional one-sided p of a rise when all events are on one page.

    Given the years of every link of the page and of its `observed` events, the
    share of all equally likely sets of as many links whose years sum to at least
    the observed sum (later years = a rising share).
    """
    sums = np.array([sum(chosen) for chosen in combinations(np.asarray(years, dtype=int), len(observed))])
    return float(np.mean(sums >= sum(observed)))


def permutation_trend(
    frame: pd.DataFrame, statistic: Callable[[pd.DataFrame], float], cluster: str, group: str,
    permutations: int = 2000, seed: int = 20261024,
) -> dict:
    """One-sided permutation p of a rise: years are shuffled between the clusters (revisions) of each group (page).

    `statistic(frame)` returns the year coefficient; the p-value is the share of
    permutations whose coefficient is at least the observed one.
    """
    observed = statistic(frame)
    clusters = frame.groupby(cluster)[[group, "year"]].first()
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(permutations):
        years = clusters["year"].copy()
        for members in clusters.groupby(group).groups.values():
            years[members] = rng.permutation(years[members].to_numpy())
        draws.append(statistic(frame.assign(year=frame[cluster].map(years))))
    return {"observed_beta": observed, "p_one_sided": float(np.mean(np.array(draws) >= observed)),
            "permutations": permutations, "seed": seed}
