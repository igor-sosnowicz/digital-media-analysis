"""External validity of H1 v2: the Reddit measure next to survey trust in the scientific community.

The General Social Survey asks about confidence in the people running the
scientific community (variable CONSCI: a great deal, only some, hardly any),
every two years. An extract downloaded by a person from the GSS Data Explorer
goes to data/external/gss_consci.csv with the columns year, response and
count (or weighted share). The comparison is a correlation of yearly values,
a check of convergent validity at the aggregate level, not a test of H1.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

from digital_media_analysis.paths import DATA_DIR

GSS_PATH = DATA_DIR / "external" / "gss_consci.csv"
GREAT_DEAL = "a great deal"
HARDLY_ANY = "hardly any"


def load_gss(path: Path = GSS_PATH) -> pd.DataFrame:
    """Per survey year: shares of 'a great deal' and 'hardly any' confidence among valid answers."""
    table = pd.read_csv(path)
    table["response"] = table["response"].str.strip().str.lower()
    valid = table[table["response"].isin([GREAT_DEAL, "only some", HARDLY_ANY])]
    totals = valid.groupby("year")["count"].sum()
    shares = valid.pivot_table(index="year", columns="response", values="count", aggfunc="sum").div(totals, axis=0)
    return pd.DataFrame({"year": shares.index, "great_deal": shares.get(GREAT_DEAL), "hardly_any": shares.get(HARDLY_ANY)}).reset_index(drop=True)


def compare(yearly: pd.DataFrame, survey: pd.DataFrame, measure: str, survey_measure: str) -> dict:
    """Pearson and Spearman correlation of a yearly Reddit share with a survey share over the common years."""
    both = yearly[["year", measure]].merge(survey[["year", survey_measure]], on="year").dropna()
    if len(both) < 3:
        return {"years": len(both), "pearson": np.nan, "pearson_p": np.nan, "spearman": np.nan, "spearman_p": np.nan}
    pearson = pearsonr(both[measure], both[survey_measure])
    spearman = spearmanr(both[measure], both[survey_measure])
    return {"years": len(both), "pearson": float(pearson.statistic), "pearson_p": float(pearson.pvalue),
            "spearman": float(spearman.statistic), "spearman_p": float(spearman.pvalue)}
