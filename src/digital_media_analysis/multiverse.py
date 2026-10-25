"""Specification curve (multiverse analysis) of the v2 hypothesis tests.

Every reasonable combination of analysis choices (definition of the outcome,
unit, period, model) is one specification; each is fitted and its trend
estimate kept, so the report can show whether the conclusion depends on the
analyst's choices. `run` takes the choices as a dict of option lists and a
function that fits one combination.
"""

from collections.abc import Callable, Mapping, Sequence
from itertools import product

import numpy as np
import pandas as pd


def specifications(choices: Mapping[str, Sequence]) -> list[dict]:
    """Every combination of the options, as dicts {choice: option}."""
    names = list(choices)
    return [dict(zip(names, combination)) for combination in product(*(choices[name] for name in names))]


def run(choices: Mapping[str, Sequence], fit: Callable[[dict], dict]) -> pd.DataFrame:
    """One row per specification: the choices and `fit`'s result (estimate, ci_low, ci_high, p_one_sided, ...).

    A specification whose fit fails is kept with its error message and no estimate.
    """
    rows = []
    for specification in specifications(choices):
        try:
            result = fit(specification)
        except Exception as error:  # noqa: BLE001 - one failing specification must not stop the curve
            result = {"estimate": np.nan, "error": f"{type(error).__name__}: {error}"}
        rows.append({**specification, **result})
    return pd.DataFrame(rows)


def summary(table: pd.DataFrame, alpha: float = 0.05) -> dict:
    """How many specifications were fitted, point in the expected direction (estimate > 1) and reject at alpha."""
    fitted = table[table["estimate"].notna()]
    return {"specifications": len(table), "fitted": len(fitted),
            "share_expected_direction": float((fitted["estimate"] > 1).mean()) if len(fitted) else np.nan,
            "share_significant": float((fitted["p_one_sided"] < alpha).mean()) if len(fitted) else np.nan,
            "median_estimate": float(fitted["estimate"].median()) if len(fitted) else np.nan}
