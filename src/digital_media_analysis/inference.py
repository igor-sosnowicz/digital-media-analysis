"""Statistical models of the extended hypothesis tests (v2, docs/hipotezy_v2.md).

Kept apart from the preregistered v1 module `hypotheses`, which stays as committed.
- `tost`: equivalence test of a trend against the smallest effect of interest,
  so "no trend" can be shown, not only "not rejected".
- `fe_logit`: weighted logistic regression with any terms, fixed effects and
  standard errors clustered by a grouping (sandwich with G/(G-1)), for trends,
  interrupted time series and difference in differences.
- `misclassified_logit` / `corrected_trend`: the trend estimated with the
  instrument's sensitivity and specificity in the likelihood,
  P(observed = 1) = (1 - spec) + (sens + spec - 1) * expit(x'b), with their
  uncertainty carried over by combining fits over draws of (sens, spec).
- `within_author_trend`: conditional logit by author (only within-author change counts).
- `rate_trend`: negative binomial (falling back to Poisson) of event counts with an exposure offset.
- `survival`: Kaplan-Meier curves, log-rank test and Cox model of how long links stay.
- `shift_share`: change of a weighted share split into within-group change and composition.
"""

from collections.abc import Sequence

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
from scipy.stats import norm

from digital_media_analysis.robustness import design_matrix


def per_year_bound(period_odds_ratio: float, period: Sequence[int]) -> float:
    """Odds ratio per year that adds up to `period_odds_ratio` between the first and last year."""
    return float(np.exp(np.log(period_odds_ratio) / max(period[1] - period[0], 1)))


def tost(beta: float, se: float, bound_odds_ratio: float, alpha: float = 0.05) -> dict:
    """Two one-sided tests that |beta| < log(bound): equivalent when both reject at `alpha`."""
    delta = np.log(bound_odds_ratio)
    p_lower = float(norm.sf((beta + delta) / se))
    p_upper = float(norm.cdf((beta - delta) / se))
    p_value = max(p_lower, p_upper)
    z = norm.ppf(1 - alpha)
    return {"bound_odds_ratio": bound_odds_ratio, "p_tost": p_value, "equivalent": bool(p_value < alpha),
            "ci90_low": float(np.exp(beta - z * se)), "ci90_high": float(np.exp(beta + z * se))}


def _cluster_covariance(design: np.ndarray, scores: np.ndarray, bread: np.ndarray, groups: np.ndarray) -> np.ndarray:
    """Sandwich covariance bread @ meat @ bread with per-group score sums and the G/(G-1) correction."""
    sums = pd.DataFrame(scores).groupby(groups).sum().to_numpy()
    count = len(sums)
    meat = sums.T @ sums * (count / (count - 1) if count > 1 else 1.0)
    return bread @ meat @ bread


def fe_logit(frame: pd.DataFrame, outcome: str, terms: Sequence[str], fixed_effects: Sequence[str] = (),
             cluster: str | None = None, weight: str | None = "weight") -> pd.DataFrame:
    """Coefficients of `terms` (log odds) with clustered standard errors; fixed-effect levels without variation are dropped.

    Columns: term, beta, se, odds_ratio, ci_low, ci_high, z, units, clusters, positives.
    """
    import statsmodels.api as sm

    data = frame.copy()
    for effect in fixed_effects:
        varying = data.groupby(effect)[outcome].transform(lambda values: values.nunique() > 1)
        data = data[varying]
    if data.empty or data[outcome].nunique() < 2:
        return pd.DataFrame([{"term": term, "beta": np.nan, "se": np.nan, "odds_ratio": np.nan, "ci_low": np.nan, "ci_high": np.nan,
                              "z": np.nan, "units": len(data), "clusters": 0, "positives": int(data[outcome].sum()) if len(data) else 0,
                              "note": "no variation in the outcome"} for term in terms])
    columns = {"const": np.ones(len(data)), **{term: data[term].astype(float).to_numpy() for term in terms}}
    design = pd.DataFrame(columns, index=data.index)
    for effect in fixed_effects:
        design = pd.concat([design, pd.get_dummies(data[effect].astype(str), prefix=f"fe_{effect}", drop_first=True, dtype=float)], axis=1)
    y = data[outcome].astype(float).to_numpy()
    w = data[weight].astype(float).to_numpy() if weight else np.ones(len(data))
    w = w / w.mean()
    fit = sm.GLM(y, design, family=sm.families.Binomial(), var_weights=w).fit()
    x = design.to_numpy()
    fitted = fit.fittedvalues.to_numpy()
    bread = np.linalg.pinv((x * (w * fitted * (1 - fitted))[:, None]).T @ x)
    groups = data[cluster].to_numpy() if cluster else np.arange(len(data))
    covariance = _cluster_covariance(x, x * (w * (y - fitted))[:, None], bread, groups)
    rows = []
    for term in terms:
        index = list(design.columns).index(term)
        beta, se = float(fit.params.iloc[index]), float(np.sqrt(covariance[index, index]))
        rows.append({"term": term, "beta": beta, "se": se, "odds_ratio": np.exp(beta), "ci_low": np.exp(beta - 1.96 * se),
                     "ci_high": np.exp(beta + 1.96 * se), "z": beta / se if se else np.nan, "units": len(data),
                     "clusters": len(np.unique(groups)), "positives": int(y.sum())})
    return pd.DataFrame(rows)


def one_sided(z: float, direction: str) -> float:
    return float(norm.sf(z) if direction == "increase" else norm.cdf(z))


def misclassified_logit(x: np.ndarray, y: np.ndarray, w: np.ndarray, sensitivity: float, specificity: float,
                        groups: np.ndarray | None = None, start: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Coefficients and clustered covariance of a logit for the true outcome, given an observed outcome with known error rates."""
    gain = sensitivity + specificity - 1
    if gain <= 0:
        raise ValueError("Sensitivity + specificity - 1 must be positive for the correction.")
    floor = 1 - specificity

    def parts(beta):
        p = expit(x @ beta)
        pi = np.clip(floor + gain * p, 1e-9, 1 - 1e-9)
        scale = w * (y / pi - (1 - y) / (1 - pi)) * gain * p * (1 - p)
        return pi, scale

    def objective(beta):
        pi, scale = parts(beta)
        return -float(np.sum(w * (y * np.log(pi) + (1 - y) * np.log(1 - pi)))), -(x.T @ scale)

    beta0 = np.zeros(x.shape[1]) if start is None else start
    result = minimize(objective, beta0, jac=True, method="BFGS", options={"gtol": 1e-7, "maxiter": 2000})
    beta = result.x
    # Observed information by central differences of the analytic gradient.
    step = 1e-5
    hessian = np.zeros((len(beta), len(beta)))
    for index in range(len(beta)):
        shift = np.zeros(len(beta))
        shift[index] = step
        hessian[:, index] = (objective(beta + shift)[1] - objective(beta - shift)[1]) / (2 * step)
    bread = np.linalg.pinv((hessian + hessian.T) / 2)
    _, scale = parts(beta)
    covariance = _cluster_covariance(x, x * scale[:, None], bread, groups if groups is not None else np.arange(len(y)))
    return beta, covariance


def corrected_trend(frame: pd.DataFrame, outcome: str, fixed_effect: str | None, cluster: str, start_year: int,
                    draws: Sequence[tuple[float, float]], weight: str = "weight") -> dict:
    """Year coefficient corrected for misclassification, combined over (sensitivity, specificity) draws by Rubin's rules.

    The first draw is the point estimate of the error rates; the others carry
    their uncertainty (e.g. from Beta posteriors of the validation counts).
    """
    design = design_matrix(frame, fixed_effect, start_year)
    x, y = design.to_numpy(), frame[outcome].astype(float).to_numpy()
    w = frame[weight].astype(float).to_numpy()
    w = w / w.mean()
    column = list(design.columns).index("year")
    betas, variances = [], []
    for sensitivity, specificity in draws:
        try:
            beta, covariance = misclassified_logit(x, y, w, sensitivity, specificity, frame[cluster].to_numpy())
        except ValueError:
            continue
        betas.append(beta[column])
        variances.append(covariance[column, column])
    if not betas:
        return {"beta": np.nan, "se": np.nan, "odds_ratio_per_year": np.nan, "ci_low": np.nan, "ci_high": np.nan, "draws": 0}
    estimate = betas[0]
    within = float(np.mean(variances))
    between = float(np.var(betas, ddof=1)) if len(betas) > 1 else 0.0
    se = float(np.sqrt(within + (1 + 1 / len(betas)) * between))
    return {"beta": estimate, "se": se, "odds_ratio_per_year": float(np.exp(estimate)), "ci_low": float(np.exp(estimate - 1.96 * se)),
            "ci_high": float(np.exp(estimate + 1.96 * se)), "draws": len(betas)}


def error_rate_draws(true_positives: int, false_negatives: int, true_negatives: int, false_positives: int,
                     count: int, seed: int) -> list[tuple[float, float]]:
    """(sensitivity, specificity): the point estimate, then `count` draws from Beta(1 + hits, 1 + misses) posteriors."""
    rng = np.random.default_rng(seed)
    point = (true_positives / max(true_positives + false_negatives, 1), true_negatives / max(true_negatives + false_positives, 1))
    sensitivity = rng.beta(1 + true_positives, 1 + false_negatives, size=count)
    specificity = rng.beta(1 + true_negatives, 1 + false_positives, size=count)
    return [point, *zip(sensitivity.tolist(), specificity.tolist())]


def within_author_trend(frame: pd.DataFrame, outcome: str, author: str, start_year: int, direction: str,
                        covariates: Sequence[str] = ()) -> dict:
    """Year coefficient of a conditional logit by author: only authors whose outcome varies inform it."""
    from statsmodels.discrete.conditional_models import ConditionalLogit

    data = frame[frame.groupby(author)[outcome].transform("nunique").gt(1)]
    exog = pd.DataFrame({"year": data["year"].astype(float) - start_year}, index=data.index)
    for covariate in covariates:
        exog = pd.concat([exog, pd.get_dummies(data[covariate].astype(str), prefix=covariate, drop_first=True, dtype=float)], axis=1)
    exog = exog.loc[:, exog.std() > 0] if len(data) else exog
    if data.empty or "year" not in exog:
        return {"odds_ratio_per_year": np.nan, "ci_low": np.nan, "ci_high": np.nan, "p_one_sided": np.nan,
                "beta": np.nan, "se": np.nan, "authors": 0, "units": 0}
    fit = ConditionalLogit(data[outcome].astype(int), exog, groups=data[author]).fit(disp=False)
    beta, se = float(fit.params["year"]), float(fit.bse["year"])
    return {"beta": beta, "se": se, "odds_ratio_per_year": np.exp(beta), "ci_low": np.exp(beta - 1.96 * se),
            "ci_high": np.exp(beta + 1.96 * se), "p_one_sided": one_sided(beta / se, direction),
            "authors": int(data[author].nunique()), "units": len(data)}


def rate_trend(panel: pd.DataFrame, events: str, exposure: str, terms: Sequence[str], fixed_effect: str | None,
               cluster: str, direction: str, term: str) -> dict:
    """Rate ratio of `term` for event counts with log(exposure) offset: negative binomial, else Poisson; clustered errors."""
    import statsmodels.api as sm

    data = panel[panel[exposure].gt(0)]
    if fixed_effect:
        data = data[data.groupby(fixed_effect)[events].transform("sum").gt(0)]
    design = pd.DataFrame({"const": 1.0, **{name: data[name].astype(float) for name in terms}}, index=data.index)
    if fixed_effect:
        design = pd.concat([design, pd.get_dummies(data[fixed_effect].astype(str), prefix="fe", drop_first=True, dtype=float)], axis=1)
    offset = np.log(data[exposure].astype(float))
    groups = data[cluster].astype("category").cat.codes.to_numpy()
    model = "negative binomial"
    try:
        fit = sm.NegativeBinomial(data[events].astype(float), design, offset=offset).fit(
            disp=False, maxiter=200, cov_type="cluster", cov_kwds={"groups": groups})
        if not np.isfinite(fit.bse[term]):
            raise ValueError("non-finite standard error")
    except Exception:  # noqa: BLE001 - any failure of the negative binomial fit falls back to Poisson
        model = "Poisson"
        fit = sm.GLM(data[events].astype(float), design, family=sm.families.Poisson(), offset=offset).fit(
            cov_type="cluster", cov_kwds={"groups": groups})
    beta, se = float(fit.params[term]), float(fit.bse[term])
    return {"model": model, "beta": beta, "se": se, "rate_ratio": np.exp(beta), "ci_low": np.exp(beta - 1.96 * se),
            "ci_high": np.exp(beta + 1.96 * se), "p_one_sided": one_sided(beta / se, direction),
            "units": len(data), "events": int(data[events].sum())}


def survival(table: pd.DataFrame, duration: str, censored: str, group: str) -> tuple[pd.DataFrame, dict]:
    """Kaplan-Meier curves per group (time, survival, ci) and the log-rank and Cox comparison of two groups."""
    from statsmodels.duration.hazard_regression import PHReg
    from statsmodels.duration.survfunc import SurvfuncRight, survdiff

    curves = []
    for name, part in table.groupby(group):
        fit = SurvfuncRight(part[duration].astype(float), (~part[censored].astype(bool)).astype(int))
        # Pointwise 95% intervals from Greenwood's variance.
        low = np.clip(fit.surv_prob - 1.96 * fit.surv_prob_se, 0, 1)
        high = np.clip(fit.surv_prob + 1.96 * fit.surv_prob_se, 0, 1)
        curves.append(pd.DataFrame({group: name, "time": fit.surv_times, "survival": fit.surv_prob, "low": low, "high": high}))
    events = (~table[censored].astype(bool)).astype(int)
    comparable = table[group].nunique() > 1 and events.sum() > 0
    statistic, p_value = survdiff(table[duration].astype(float), events, table[group]) if comparable else (np.nan, np.nan)
    hazard = {}
    if comparable and table[group].nunique() == 2:
        exog = pd.get_dummies(table[group], drop_first=True, dtype=float)
        try:
            fit = PHReg(table[duration].astype(float), exog, status=events).fit()
            hazard = {"term": exog.columns[0], "hazard_ratio": float(np.exp(fit.params[0])),
                      "ci_low": float(np.exp(fit.params[0] - 1.96 * fit.bse[0])), "ci_high": float(np.exp(fit.params[0] + 1.96 * fit.bse[0]))}
        except np.linalg.LinAlgError:
            hazard = {"term": exog.columns[0], "note": "Cox model not estimable (singular information)"}
    return (pd.concat(curves, ignore_index=True) if curves else pd.DataFrame()), {"logrank": float(statistic), "p_value": float(p_value), **hazard}


def shift_share(frame: pd.DataFrame, outcome: str, group: str, first: Sequence[int], last: Sequence[int]) -> dict:
    """Change of the weighted share of `outcome` between two periods = within-group change + composition change."""
    def summary(period):
        part = frame[frame["year"].between(*period)]
        weights = part.groupby(group)["weight"].sum()
        shares = part.groupby(group).apply(lambda cell: (cell["weight"] * cell[outcome]).sum() / cell["weight"].sum(), include_groups=False)
        return weights / weights.sum(), shares

    w1, p1 = summary(first)
    w2, p2 = summary(last)
    groups = w1.index.union(w2.index)
    w1, w2 = w1.reindex(groups, fill_value=0.0), w2.reindex(groups, fill_value=0.0)
    p1, p2 = p1.reindex(groups), p2.reindex(groups)
    p1, p2 = p1.fillna(p2), p2.fillna(p1)
    total = float((w2 * p2).sum() - (w1 * p1).sum())
    within = float((((w1 + w2) / 2) * (p2 - p1)).sum())
    composition = float((((p1 + p2) / 2) * (w2 - w1)).sum())
    return {"first_share": float((w1 * p1).sum()), "last_share": float((w2 * p2).sum()), "total": total,
            "within": within, "composition": composition}
