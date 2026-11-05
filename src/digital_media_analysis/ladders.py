"""Hypothesis ladders of v2 and their power gate (docs/plan_poprawy_krok_po_kroku.md, sections 3 and 4, step 7).

Each family (H1, H2) lists variants from the claim closest to the preregistered hypothesis to the weakest. Before the
confirmatory run the power gate takes nuisance values that reveal no trend: units, the instrument's sensitivity and
specificity, the pooled base share and the design effect of clusters (computed without the year). It makes the first
variant of each ladder that passed its validity gate and reaches the target power, both to detect the smallest effect
of interest and, where the decision rule has one, to show its absence (TOST), the primary test of the family. The two
primary tests get Holm's correction; the other powered variants are secondary, with Holm within their family; the rest
are reported as descriptive. Level hypotheses (H2-S4, H2-S5) take their power from planning shares fixed before the
data, because the observed share is their result.

The module also holds the exclusions of the plan (step 1.5): units of v1 (posts of the v1 Reddit frames with their
comments, the eight v1 Wikipedia pages), so hypotheses inspired by v1 are tested on other data, and bulk revisions
that add many links at once (imports, translations).
"""

from collections.abc import Iterable, Mapping
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit, logit
from scipy.stats import binomtest, norm

from digital_media_analysis import power

LADDERS = {"H1": ["H1", "H1-S1", "H1-S2", "H1-S3"], "H2": ["H2", "H2-S1", "H2-S2", "H2-S4"]}
SECONDARY_ONLY = {"H1": [], "H2": ["H2-S3", "H2-S5"]}
TARGET_POWER = 0.8
NON_SPECIALIST = ["media", "social_blog", "other"]
SPECIALIST = ["scientific", "institutional", "encyclopedia"]
INSTITUTION = "institution"


# --- Exclusions (step 1.5) ----------------------------------------------------------------------------------------


def v1_post_ids(frame_dirs: Iterable[Path]) -> set[str]:
    """Ids of every post of the v1 Reddit frames (posts-<year>.csv files)."""
    ids: set[str] = set()
    for folder in frame_dirs:
        for path in sorted(Path(folder).glob("posts-*.csv")):
            ids |= set(pd.read_csv(path, dtype=str, usecols=["id"])["id"].dropna())
    return ids


def without_v1_posts(units: pd.DataFrame, v1_ids: set[str]) -> pd.DataFrame:
    """Units whose post (the unit itself or the post a comment answers) was not in a v1 frame."""
    return units[~units["post_id"].astype(str).isin(v1_ids)].reset_index(drop=True)


def without_pages(links: pd.DataFrame, titles: Iterable[str]) -> pd.DataFrame:
    return links[~links["title"].isin(set(titles))].reset_index(drop=True)


def without_bulk(links: pd.DataFrame, limit: int, revision: str = "revid") -> pd.DataFrame:
    """Links of revisions that add at most `limit` links of the table (bulk revisions are imports or translations)."""
    return links[links.groupby(revision)["url"].transform("size") <= limit].reset_index(drop=True)


# --- Power of a variant and the gate (step 7) ----------------------------------------------------------------------


def variant_power(spec: Mapping, alpha: float = 0.05) -> dict:
    """Power to detect the smallest effect of interest and, for trends and differences, TOST power under no effect."""
    test, design = spec["test"], spec.get("design_effect", 1.0)
    if test == "trend":
        slope = np.log(spec["sesoi_period_odds_ratio"]) / (spec["years"] - 1)
        args = (spec["units"], spec["share"], slope, spec["years"], spec.get("sensitivity", 1.0), spec.get("specificity", 1.0), design)
        return {"power": power.trend_power(*args, alpha=alpha), "power_equivalence": power.equivalence_power(*args, alpha=alpha)}
    if test == "two_shares":
        # The smallest odds ratio of interest split around the pooled share; equivalence on the log-odds scale.
        share, bound = spec["share"], np.log(spec["sesoi_odds_ratio"])
        first, second = expit(logit(share) + bound / 2), expit(logit(share) - bound / 2)
        detect = power.two_share_power(first, second, spec["units_first"], spec["units_second"], design, alpha)
        error = np.sqrt(design * (1 / spec["units_first"] + 1 / spec["units_second"]) / (share * (1 - share)))
        return {"power": detect, "power_equivalence": float(max(0.0, 2 * norm.cdf(bound / error - norm.ppf(1 - alpha)) - 1))}
    if test == "bound":
        return {"power": power.bound_power(spec["units"], spec["planning_share"], spec["bound"], design, alpha), "power_equivalence": None}
    if test == "cox":
        exposed = spec["exposed_share"]
        z = np.sqrt(spec["events"] * exposed * (1 - exposed)) * abs(np.log(spec["hazard_ratio"]))
        return {"power": float(norm.cdf(z - norm.ppf(1 - alpha))), "power_equivalence": None}
    if test == "binomial":
        return {"power": power.binomial_power(int(spec["units"]), spec["planning_share"], spec["null_share"], alpha), "power_equivalence": None}
    raise ValueError(f"Unknown test {test!r} of variant {spec.get('variant')!r}.")


def gate(variants: Mapping[str, Mapping], target: float = TARGET_POWER, ladders: Mapping[str, list[str]] = LADDERS,
         secondary_only: Mapping[str, list[str]] = SECONDARY_ONLY) -> dict:
    """Primary, secondary and descriptive variants of each family (rule of section 4 of the plan)."""
    result = {}
    for family, ladder in ladders.items():
        checked = {}
        for name in [*ladder, *secondary_only.get(family, [])]:
            spec = variants.get(name) or {"valid": False, "reason": "brak danych do wyliczenia mocy"}
            powers = variant_power(spec) if spec.get("valid") else {"power": None, "power_equivalence": None}
            passed = bool(spec.get("valid")) and powers["power"] >= target and (
                powers["power_equivalence"] is None or powers["power_equivalence"] >= target)
            checked[name] = {**{key: value for key, value in spec.items() if key != "valid"}, **powers,
                             "valid": bool(spec.get("valid")), "passed": bool(passed)}
        primary = next((name for name in ladder if checked[name]["passed"]), None)
        result[family] = {"primary": primary, "secondary": [name for name, item in checked.items() if item["passed"] and name != primary],
                          "descriptive": [name for name, item in checked.items() if not item["passed"]], "variants": checked}
    return result


def roles(decision: Mapping) -> dict[str, str]:
    """Variant -> primary, secondary or descriptive, from a gate decision."""
    found = {}
    for family in decision.values():
        found |= {name: "descriptive" for name in family["descriptive"]}
        found |= {name: "secondary" for name in family["secondary"]}
        if family["primary"]:
            found[family["primary"]] = "primary"
    return found


def holm(p_values: Mapping[str, float]) -> dict[str, float]:
    """Holm's step-down adjusted p-values; missing values stay missing and do not count."""
    present = sorted(((value, key) for key, value in p_values.items() if value is not None and np.isfinite(value)))
    adjusted, running = {}, 0.0
    for rank, (value, key) in enumerate(present):
        running = max(running, min(1.0, (len(present) - rank) * value))
        adjusted[key] = running
    return {key: adjusted.get(key, np.nan) for key in p_values}


# --- Tests of the level variants ------------------------------------------------------------------------------------


def share_below(values: pd.Series, clusters: pd.Series, bound: float) -> dict:
    """One-sided test that a share lies below `bound`, with a cluster-robust standard error of the ratio estimator."""
    y = values.astype(float).to_numpy()
    share = float(y.mean())
    residuals = pd.Series(y - share).groupby(np.asarray(clusters)).sum()
    error = float(np.sqrt((residuals**2).sum()) / len(y))
    z = (share - bound) / error if error > 0 else (-np.inf if share < bound else np.inf)
    return {"estimate": share, "se": error, "ci_high": share + norm.ppf(0.95) * error, "z": z,
            "p_one_sided": float(norm.cdf(z)), "units": len(y), "events": int(y.sum()), "clusters": int(residuals.size)}


def share_above(successes: int, trials: int, null_share: float) -> dict:
    """Exact one-sided binomial test that a share exceeds `null_share`."""
    if trials == 0:
        return {"estimate": np.nan, "p_one_sided": np.nan, "units": 0, "events": 0}
    test = binomtest(successes, trials, null_share, alternative="greater")
    low = test.proportion_ci(confidence_level=0.90).low
    return {"estimate": successes / trials, "ci_low": float(low), "ci_high": 1.0, "p_one_sided": float(test.pvalue),
            "units": trials, "events": successes}


def attenuated_bound(bound_odds_ratio: float, observed_share: float, sensitivity: float, specificity: float) -> float:
    """The equivalence bound on the scale the instrument sees: an instrument with errors flattens every trend, so TOST
    against the unflattened bound would show "no trend" too easily (the bound shrinks by the same factor as the slope)."""
    true = float(np.clip((observed_share - (1 - specificity)) / (sensitivity + specificity - 1), 1e-6, 1 - 1e-6))
    seen = power.observed_share(true, sensitivity, specificity)
    factor = (sensitivity + specificity - 1) * true * (1 - true) / (seen * (1 - seen))
    return float(np.exp(np.log(bound_odds_ratio) * factor))
