"""Tests of the research hypotheses (docs/hipotezy.md): analysis samples, outcomes, yearly shares and trends.

H1 (Reddit, 2005-2018, declining trust in the scientific consensus):
- H1-A: share of posts that challenge the consensus among posts about science
  (`consensus_stance` from instrument stance_v1), expected to rise;
- H1-B: among posts citing a source, the share citing consensus sources
  (scientific, institutional; expected to fall) and alternative sources
  (social_blog, unknown, personal; expected to rise), from instrument gliner_v1.
H2 (Wikipedia, 2020-2026, more references to alternative sources): share of
links added to references whose domain is an alternative source (social_blog),
expected to rise.

Each trend is the year coefficient of a weighted logistic regression with
fixed effects for the subreddit (H1) or page (H2) and standard errors clustered
by sampled day (H1) or revision (H2); the preregistered test is one-sided.
Yearly shares come with bootstrap intervals. Instrument error is corrected in
the yearly shares (Rogan-Gladen) where the gold standard gives error rates.
"""

from collections.abc import Callable, Sequence
from pathlib import Path

import numpy as np
import pandas as pd

from digital_media_analysis.instruments.labels import LABEL_SEPARATOR

SEED = 20261024
BOOTSTRAP_SAMPLES = 1000


def cached_scores(path: Path, units: pd.DataFrame, score: Callable[[pd.DataFrame], pd.DataFrame], refresh: bool = False) -> pd.DataFrame:
    """Model output for `units`, read from `path` when it covers exactly these units, else computed and saved."""
    wanted = set(units["unit_id"].astype(str))
    if path.exists() and not refresh:
        cached = pd.read_csv(path, dtype={"unit_id": str}, keep_default_na=False)
        if set(cached["unit_id"]) == wanted:
            return cached
    output = score(units)
    path.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(path, index=False, encoding="utf-8")
    return output


def in_years(frame: pd.DataFrame, period: Sequence[int]) -> pd.DataFrame:
    first, last = period
    return frame[frame["year"].between(first, last)]


def h1_analysis_sample(frame: pd.DataFrame, subreddits: Sequence[str], period: Sequence[int], per_cell: int, seed: int = SEED) -> pd.DataFrame:
    """Simple random sample of at most `per_cell` posts per subreddit and year, with weights back to all posts.

    `frame` holds frame posts (gold.reddit_units of the frame): unit_id, group
    (subreddit), year, introduced, day_weight. The weight of a sampled post is
    its day weight times the subreddit-year's frame posts over the posts sampled.
    """
    listed = {name.casefold() for name in subreddits}
    eligible = in_years(frame[frame["group"].str.casefold().isin(listed)], period)
    rng = np.random.default_rng(seed)
    parts = []
    for (subreddit, year), cell in eligible.groupby(["group", "year"], sort=True):
        chosen = cell if len(cell) <= per_cell else cell.sample(n=per_cell, random_state=rng)
        parts.append(chosen.assign(N_cell=len(cell), n_cell=len(chosen)))
    sample = pd.concat(parts, ignore_index=True)
    sample["day"] = sample["introduced"].str[:10]
    sample["weight"] = sample["day_weight"].astype(float) * sample["N_cell"] / sample["n_cell"]
    return sample[["unit_id", "group", "year", "day", "day_weight", "N_cell", "n_cell", "weight"]]


def has_any(source_types: pd.Series, codes: Sequence[str]) -> pd.Series:
    wanted = set(codes)
    return source_types.fillna("").map(lambda text: int(bool(wanted & set(str(text).split(LABEL_SEPARATOR)))))


def h1b_outcomes(labels: pd.DataFrame, consensus: Sequence[str], alternative: Sequence[str]) -> pd.DataFrame:
    """Per citing post: `consensus` and `alternative` indicators (posts without a source are left out)."""
    citing = labels[labels["cites_source"].astype(int).eq(1)]
    return citing.assign(consensus=has_any(citing["source_types"], consensus), alternative=has_any(citing["source_types"], alternative))


def h1a_outcomes(stances: pd.DataFrame) -> pd.DataFrame:
    """Per post about science (stance other than not_applicable): `challenges` and `supports` indicators."""
    relevant = stances[stances["consensus_stance"].ne("not_applicable")]
    return relevant.assign(
        challenges=relevant["consensus_stance"].eq("challenges").astype(int),
        supports=relevant["consensus_stance"].eq("supports").astype(int),
    )


def h2_outcomes(links: pd.DataFrame, period: Sequence[int], alternative: Sequence[str]) -> pd.DataFrame:
    """Added reference links in the period with an `alternative` indicator and the revision as cluster."""
    within = in_years(links.dropna(subset=["year"]).astype({"year": int}), period)
    return within.assign(
        alternative=within["category"].isin(alternative).astype(int),
        revision=within["page"] + "#" + within["revision_number"].astype(str),
        weight=1.0,
    )


def rogan_gladen(observed: float, sensitivity: float, specificity: float) -> float:
    """Prevalence corrected for misclassification, clipped to [0, 1]; missing when the test is uninformative."""
    informative = sensitivity + specificity - 1
    if np.isnan(sensitivity) or np.isnan(specificity) or informative <= 0:
        return np.nan
    return float(np.clip((observed + specificity - 1) / informative, 0, 1))


def error_rates(truth: pd.Series, predicted: pd.Series, weights: pd.Series | None = None) -> dict[str, float]:
    """Weighted sensitivity and specificity of a binary indicator, with the number of true positives and negatives."""
    y, p = truth.astype(int).to_numpy().astype(bool), predicted.astype(int).to_numpy().astype(bool)
    w = np.ones(len(y)) if weights is None else weights.to_numpy(float)
    positives, negatives = w[y].sum(), w[~y].sum()
    return {
        "sensitivity": (w[y & p].sum() / positives) if positives else np.nan,
        "specificity": (w[~y & ~p].sum() / negatives) if negatives else np.nan,
        "positives": int(y.sum()),
        "negatives": int((~y).sum()),
    }


def yearly_shares(
    frame: pd.DataFrame, outcome: str, by: Sequence[str] = (), strata: Sequence[str] = ("year",),
    samples: int = BOOTSTRAP_SAMPLES, seed: int = SEED,
) -> pd.DataFrame:
    """Weighted share of `outcome` per year (and `by` groups) with percentile bootstrap intervals within `strata`."""
    groups = ["year", *by]
    rng = np.random.default_rng(seed)
    rows = []
    for key, group in frame.groupby(groups, sort=True):
        key = key if isinstance(key, tuple) else (key,)
        y, w = group[outcome].to_numpy(float), group["weight"].to_numpy(float)
        share = (w * y).sum() / w.sum()
        cells = [cell.index.to_numpy() for _, cell in group.groupby(list(strata))]
        draws = []
        for _ in range(samples):
            rows_drawn = np.concatenate([rng.choice(index, size=len(index), replace=True) for index in cells])
            drawn = frame.loc[rows_drawn]
            draws.append((drawn["weight"] * drawn[outcome]).sum() / drawn["weight"].sum())
        low, high = np.quantile(draws, [0.025, 0.975]) if draws else (np.nan, np.nan)
        rows.append({**dict(zip(groups, key)), "share": share, "low": low, "high": high, "units": len(group)})
    return pd.DataFrame(rows)


def trend(
    frame: pd.DataFrame, outcome: str, fixed_effect: str | None, cluster: str, direction: str, start_year: int,
) -> dict:
    """Year coefficient of a weighted logistic regression with fixed effects and clustered errors, tested one-sided.

    `direction` is "increase" or "decrease". The sampling weights enter as variance
    weights scaled to mean 1 (a weighted pseudo-likelihood), so they set relative
    importance without inflating the sample size, and the clustered sandwich
    errors stay valid.
    """
    import statsmodels.api as sm

    data = frame.dropna(subset=[outcome, "year", "weight"]).copy()
    result = {"outcome": outcome, "direction": direction, "units": len(data), "clusters": data[cluster].nunique(),
              "positives": int(data[outcome].sum()), "beta": np.nan, "se": np.nan, "odds_ratio_per_year": np.nan,
              "ci_low": np.nan, "ci_high": np.nan, "p_one_sided": np.nan, "note": ""}
    if data[outcome].nunique() < 2:
        result["note"] = "brak zmienności wyniku"
        return result
    design = pd.DataFrame({"const": 1.0, "year": data["year"].astype(float) - start_year}, index=data.index)
    if fixed_effect:
        # Levels whose outcome never varies cannot be estimated and are dropped.
        varying = data.groupby(fixed_effect)[outcome].transform("nunique").gt(1)
        data, design = data[varying], design[varying]
        dummies = pd.get_dummies(data[fixed_effect], prefix="fe", drop_first=True, dtype=float)
        design = pd.concat([design, dummies], axis=1)
    weights = data["weight"] / data["weight"].mean()
    try:
        fit = sm.GLM(data[outcome].astype(float), design, family=sm.families.Binomial(), var_weights=weights).fit()
    except Exception as error:  # separation or a singular design: report, do not guess
        result["note"] = f"model nie zbiegł: {error}"
        return result
    beta = float(fit.params["year"])
    se = _clustered_se(design, data[outcome].to_numpy(float), weights.to_numpy(float), fit.fittedvalues.to_numpy(float),
                       pd.factorize(data[cluster])[0], list(design.columns).index("year"))
    from scipy.stats import norm

    z = beta / se if se else np.nan
    p = norm.sf(z) if direction == "increase" else norm.cdf(z)
    result.update({
        "units": len(data), "clusters": data[cluster].nunique(), "positives": int(data[outcome].sum()),
        "beta": beta, "se": se, "odds_ratio_per_year": float(np.exp(beta)),
        "ci_low": float(np.exp(beta - 1.96 * se)), "ci_high": float(np.exp(beta + 1.96 * se)), "p_one_sided": float(p),
    })
    return result


def _clustered_se(design: pd.DataFrame, y: np.ndarray, w: np.ndarray, fitted: np.ndarray, groups: np.ndarray, column: int) -> float:
    """Cluster-robust (sandwich) standard error of one coefficient of a weighted logistic regression.

    A = X' diag(w p (1 - p)) X is the weighted information, B sums the weighted
    scores within clusters; V = A^-1 B A^-1 with the small-sample factor G / (G - 1).
    """
    x = design.to_numpy(float)
    information = (x * (w * fitted * (1 - fitted))[:, None]).T @ x
    scores = x * (w * (y - fitted))[:, None]
    clusters = int(groups.max()) + 1
    summed = np.zeros((clusters, x.shape[1]))
    np.add.at(summed, groups, scores)
    meat = summed.T @ summed * (clusters / (clusters - 1) if clusters > 1 else np.nan)
    bread = np.linalg.pinv(information)
    variance = bread @ meat @ bread
    return float(np.sqrt(variance[column, column]))

