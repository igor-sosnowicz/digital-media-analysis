"""Exploratory robustness analyses of the hypothesis tests (not preregistered; docs/wyniki_hipotez.md).

Kept apart from the preregistered `hypotheses` module, so the confirmatory code
stays as committed. Firth's penalised logistic regression handles rare events
and separation: it maximises the log-likelihood plus half the log-determinant
of the Fisher information (Jeffreys prior), which keeps estimates finite and
reduces their small-sample bias, so fixed-effect levels without any event can
stay in the model. Its test is the penalised likelihood-ratio test.
"""

from collections.abc import Sequence

import numpy as np
import pandas as pd
from scipy.stats import chi2


def _penalised_loglik(x: np.ndarray, y: np.ndarray, beta: np.ndarray) -> float:
    eta = x @ beta
    loglik = float(np.sum(y * eta - np.logaddexp(0, eta)))
    p = 1 / (1 + np.exp(-eta))
    information = (x * (p * (1 - p))[:, None]).T @ x
    sign, logdet = np.linalg.slogdet(information)
    return loglik + 0.5 * logdet if sign > 0 else -np.inf


def firth_logit(x: np.ndarray, y: np.ndarray, max_iter: int = 200, tol: float = 1e-8) -> tuple[np.ndarray, np.ndarray, float]:
    """Coefficients, their covariance (inverse information) and the penalised log-likelihood of Firth's logit."""
    beta = np.zeros(x.shape[1])
    current = _penalised_loglik(x, y, beta)
    for _ in range(max_iter):
        p = 1 / (1 + np.exp(-(x @ beta)))
        w = p * (1 - p)
        inverse = np.linalg.pinv((x * w[:, None]).T @ x)
        leverage = w * np.einsum("ij,jk,ik->i", x, inverse, x)
        step = inverse @ (x.T @ (y - p + leverage * (0.5 - p)))
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


def design_matrix(frame: pd.DataFrame, fixed_effect: str | None, start_year: int, with_year: bool = True) -> pd.DataFrame:
    columns = {"const": np.ones(len(frame))}
    if with_year:
        columns["year"] = frame["year"].astype(float).to_numpy() - start_year
    design = pd.DataFrame(columns, index=frame.index)
    if fixed_effect:
        design = pd.concat([design, pd.get_dummies(frame[fixed_effect], prefix="fe", drop_first=True, dtype=float)], axis=1)
    return design


def firth_trend(frame: pd.DataFrame, outcome: str, fixed_effect: str | None, direction: str, start_year: int) -> dict:
    """Year coefficient of Firth's logit with fixed effects (all levels kept), tested one-sided by penalised LR."""
    y = frame[outcome].to_numpy(float)
    full = design_matrix(frame, fixed_effect, start_year)
    beta, covariance, loglik = firth_logit(full.to_numpy(), y)
    _, _, restricted = firth_logit(design_matrix(frame, fixed_effect, start_year, with_year=False).to_numpy(), y)
    column = list(full.columns).index("year")
    estimate, se = float(beta[column]), float(np.sqrt(covariance[column, column]))
    statistic = max(2 * (loglik - restricted), 0.0)
    two_sided = float(chi2.sf(statistic, 1))
    toward = estimate > 0 if direction == "increase" else estimate < 0
    return {
        "beta": estimate, "se": se, "odds_ratio_per_year": float(np.exp(estimate)),
        "ci_low": float(np.exp(estimate - 1.96 * se)), "ci_high": float(np.exp(estimate + 1.96 * se)),
        "p_one_sided": two_sided / 2 if toward else 1 - two_sided / 2,
        "units": len(frame), "positives": int(y.sum()), "lr_statistic": statistic,
    }


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
