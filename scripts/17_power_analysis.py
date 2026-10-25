"""Power analysis of the v2 hypothesis tests (docs/hipotezy_v2.md), by simulation; uses no v2 data.

Planning values: H1 has 13 subreddits and 14 years; the base share of
`challenges` among units about a consensus topic is unknown before the v2 data,
so it is varied (0.05, 0.15, 0.30). H2's base share of alternative links is
0.0075, the rate in the v1 data of eight pages (2020-2026). The trend to
detect is the smallest effect of interest of config.yaml (`hypotheses_v2`); the
equivalence power is that of TOST when the true trend is zero. Writes
annotations/hypotheses_v2/power_h1.csv, power_h2.csv and their charts.
"""

import argparse

import matplotlib

matplotlib.use("Agg")

import pandas as pd  # noqa: E402

from digital_media_analysis import charts, inference, power  # noqa: E402
from digital_media_analysis.config_reader import get_hypotheses_v2  # noqa: E402
from digital_media_analysis.paths import HYPOTHESES_V2_DIR  # noqa: E402

H1_BASE_RATES = [0.05, 0.15, 0.30]
H1_PER_CELL = [10, 25, 50, 100, 200]
H2_BASE_RATE = 0.0075
H2_PAGES = 200
H2_PER_CELL = [2, 5, 10, 20, 40]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replicates", type=int, default=200)
    args = parser.parse_args()
    settings = get_hypotheses_v2()
    figures = HYPOTHESES_V2_DIR / "figures"
    figures.mkdir(parents=True, exist_ok=True)

    h1 = settings["h1"]
    years = h1["period"][1] - h1["period"][0] + 1
    bound = inference.per_year_bound(h1["sesoi_period_odds_ratio"], h1["period"])
    tables = [power.curve(len(h1["subreddits"]), years, H1_PER_CELL, rate, bound, bound, args.replicates).assign(base_rate=rate)
              for rate in H1_BASE_RATES]
    h1_table = pd.concat(tables, ignore_index=True).assign(hypothesis="H1", odds_ratio_per_year=bound)
    h1_table.to_csv(HYPOTHESES_V2_DIR / "power_h1.csv", index=False, encoding="utf-8")
    charts.power_curves(h1_table[h1_table["base_rate"].eq(0.15)].rename(columns={"per_cell": "jednostki na subreddit i rok"}),
                        "jednostki na subreddit i rok", planned=h1["units_per_cell"], path=figures / "power_h1.png")

    h2 = settings["h2"]
    years = h2["period"][1] - h2["period"][0] + 1
    bound2 = inference.per_year_bound(h2["sesoi_period_odds_ratio"], h2["period"])
    h2_table = power.curve(H2_PAGES, years, H2_PER_CELL, H2_BASE_RATE, bound2, bound2, args.replicates, fixed_effects=False)
    h2_table = h2_table.assign(hypothesis="H2", odds_ratio_per_year=bound2, links=lambda frame: frame["units"])
    h2_table.to_csv(HYPOTHESES_V2_DIR / "power_h2.csv", index=False, encoding="utf-8")
    charts.power_curves(h2_table.rename(columns={"units": "dodane linki (wszystkie strony i lata)"}),
                        "dodane linki (wszystkie strony i lata)", path=figures / "power_h2.png")
    for table in (h1_table, h2_table):
        print(table[["hypothesis", "base_rate", "per_cell", "units", "power", "power_equivalence", "false_positive_rate"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
