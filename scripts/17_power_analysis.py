"""Power analysis of the v2 hypothesis tests (docs/hipotezy_v2.md), by simulation; uses no v2 data.

Planning values: H1 has 13 subreddits and 14 years; the base share of
`challenges` among units about a consensus topic is unknown before the v2 data,
so it is varied (0.05, 0.15, 0.30). H2's base share of alternative links is
0.0075, the rate in the v1 data of eight pages (2020-2026). The trend to
detect is the smallest effect of interest of config.yaml (`hypotheses_v2`); the
equivalence power is that of TOST when the true trend is zero. Writes
annotations/hypotheses_v2/power_h1.csv, power_h2.csv and their charts.

`--plan` also writes the planning grid of docs/plan_poprawy_krok_po_kroku.md
(sections 1.3 and 3): power of every variant of the hypothesis ladders with
instrument error and a design effect, from planning values measured on v1 data
without any trend (power_plan_values.json, power_plan.csv). `--check` compares
the planning formula with the simulation in two settings.
"""

import argparse
import json

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pandas as pd

from digital_media_analysis import (
    charts,
    inference,
    power,
    stance,
    wikipedia_refs,
)
from digital_media_analysis.config_reader import get_hypotheses_v2
from digital_media_analysis.paths import HYPOTHESES_DIR, HYPOTHESES_V2_DIR

H1_BASE_RATES = [0.05, 0.15, 0.30]
H1_PER_CELL = [10, 25, 50, 100, 200]
H2_BASE_RATE = 0.0075
H2_PAGES = 200
H2_PER_CELL = [2, 5, 10, 20, 40]

# Planning grid. Instruments of the stance outcome: v1's stance_v1 on the test split (precision 0.80, recall 0.21,
# so specificity about 0.987) and the targets of gate B6.
PLAN_STANCE_INSTRUMENTS = {"perfect": (1.0, 1.0), "stance_v1": (0.21, 0.987), "Se 0.6, Sp 0.97": (0.6, 0.97),
                           "Se 0.7, Sp 0.98 (gate B6)": (0.7, 0.98), "Se 0.85, Sp 0.98": (0.85, 0.98)}
PLAN_H1_UNITS = [20_000, 40_000, 70_000, 100_000]
PLAN_H2_UNITS = [1_500, 4_000, 10_000, 45_000]
# v1 (scripts/10): 2 of the 10 alternative links by domain stay alternative when the owner of the post is read.
ALT_OWNER_KEPT = 2 / 10
# Revisions adding more than this many links (imports, translations) leave the main H2 analysis (step 1.5).
BULK_LINKS = 20
# Assumptions without v1 data, named in the plan: participation share of the questioning subreddits among consensus
# units, the control group's share of non-specialist sources and the population-level change seen in v1 exploration.
PARTICIPATION_SHARE = 0.10
CONTROL_NON_SPECIALIST = 0.30
V1_POPULATION_ODDS_RATIO = 1.65
MARGINAL_SHARE = 0.02


def planning_values() -> dict:
    """Levels and design effects measured on v1 data, without estimating any trend."""
    trends = pd.read_csv(HYPOTHESES_DIR / "confirmatory_trends.csv")
    alternative = trends[trends["hypothesis"].eq("H1-B") & trends["analysis"].eq("primary") & trends["outcome"].eq("alternative")].iloc[0]
    audit = pd.read_csv(HYPOTHESES_DIR / "audit_error_rates.csv")
    gliner = audit[audit["source"].eq("pooled") & audit["indicator"].eq("alternative")].iloc[0]
    observed = alternative["positives"] / alternative["units"]
    true_share = (observed - (1 - gliner["specificity"])) / (gliner["sensitivity"] + gliner["specificity"] - 1)
    # Design effect implied by the v1 standard error of the H1-B trend (clustering by day, weights, fixed effects).
    implied = alternative["se"] ** 2 * alternative["units"] * observed * (1 - observed) * power.year_variance(14)

    kept, _ = stance.reference(stance.load_labels("gold"))
    applicable = kept[kept[stance.STANCE].ne("not_applicable")]

    links = wikipedia_refs.load_added_links()
    links = links[links["year"].between(2020, 2026)].copy()
    links["revision"] = links["page"] + "#" + links["revision_number"].astype(str)
    small = links[links.groupby("revision")["url"].transform("size") <= BULK_LINKS]
    non_specialist = small["category"].isin(["media", "social_blog", "other"]).astype(float)
    effects = {name: power.design_effect(frame["category"].isin(["media", "social_blog", "other"]).astype(float), frame["revision"])
               for name, frame in (("all_revisions", links), ("without_bulk_revisions", small))}
    alt_domain = float(links["category"].eq("social_blog").mean())
    return {
        "h1_stance_share_challenges": float(applicable[stance.STANCE].eq("challenges").mean()),
        "h1_stance_units_with_stance": len(applicable),
        "h1_alternative_observed_share": float(observed),
        "h1_alternative_true_share": float(true_share),
        "h1_gliner_alternative_sensitivity": float(gliner["sensitivity"]),
        "h1_gliner_alternative_specificity": float(gliner["specificity"]),
        "h1_implied_design_effect": float(implied),
        "h2_links_2020_2026": len(links),
        "h2_links_per_page_year": float(len(links) / links["page"].nunique() / 7),
        "h2_alt_domain_share": alt_domain,
        "h2_alt_owner_share": alt_domain * ALT_OWNER_KEPT,
        "h2_non_specialist_share_without_bulk": float(non_specialist.mean()),
        "h2_design_effect": {name: {key: round(value, 4) if isinstance(value, float) else value for key, value in effect.items()}
                             for name, effect in effects.items()},
    }


def trend_rows(variant: str, scenario: str, share: float, years: int, odds_ratio: float, units: list[int],
               sensitivity: float = 1.0, specificity: float = 1.0, design_effect: float = 1.0, effect: float | None = None) -> list[dict]:
    """Rows of a trend variant: power for the true effect (default: the SESOI), TOST power under no trend, units needed."""
    bound = np.log(odds_ratio) / (years - 1)
    slope = np.log(effect) / (years - 1) if effect else bound
    common = {"variant": variant, "scenario": scenario, "test": "trend", "share": share, "sensitivity": sensitivity,
              "specificity": specificity, "design_effect": design_effect, "years": years, "sesoi_period_odds_ratio": odds_ratio,
              "effect_period_odds_ratio": effect or odds_ratio,
              "units_needed": power.units_needed(share, slope, years, sensitivity, specificity, design_effect),
              "units_needed_equivalence": power.units_needed(share, bound, years, sensitivity, specificity, design_effect, equivalence=True)}
    return [{**common, "units": n, "power": power.trend_power(n, share, slope, years, sensitivity, specificity, design_effect),
             "power_equivalence": power.equivalence_power(n, share, bound, years, sensitivity, specificity, design_effect)} for n in units]


def plan_table(values: dict) -> pd.DataFrame:
    rows = []
    implied = round(values["h1_implied_design_effect"], 2)
    for share in (0.05, 0.10, 0.15):
        for name, (sensitivity, specificity) in PLAN_STANCE_INSTRUMENTS.items():
            for effect in (2.0, implied):
                rows += trend_rows("H1", name, share, 14, 1.25, PLAN_H1_UNITS, sensitivity, specificity, effect)
    gliner = (values["h1_gliner_alternative_sensitivity"], values["h1_gliner_alternative_specificity"])
    for effect in (2.0, implied):
        rows += trend_rows("H1-S1", "GLiNER, alternative sources", values["h1_alternative_true_share"], 14, 1.25, PLAN_H1_UNITS, *gliner, effect)
        rows += trend_rows("H1-S2", "GLiNER, effect = SESOI", values["h1_alternative_true_share"], 14, 1.25, PLAN_H1_UNITS, *gliner, effect)
        rows += trend_rows("H1-S2", "GLiNER, effect as in v1 exploration", values["h1_alternative_true_share"], 14, 1.25,
                           [5_000, 10_000, 20_000], *gliner, effect, effect=V1_POPULATION_ODDS_RATIO)
    rows += trend_rows("H1-S3", "topic counts, no labels", PARTICIPATION_SHARE, 14, 1.25, [10_000, 30_000, 60_000], design_effect=1.5)

    h2_effect = round(values["h2_design_effect"]["without_bulk_revisions"]["design_effect"], 2)
    for name, share in (("alternative by owner", values["h2_alt_owner_share"]), ("alternative by domain", values["h2_alt_domain_share"])):
        for effect in (1.0, h2_effect):
            rows += trend_rows("H2", name, share, 7, 1.5, PLAN_H2_UNITS, design_effect=effect)
    non_specialist = values["h2_non_specialist_share_without_bulk"]
    for name, (sensitivity, specificity) in (("domain category", (1.0, 1.0)), ("domain category, Se 0.95, Sp 0.95", (0.95, 0.95))):
        rows += trend_rows("H2-S1", name, non_specialist, 7, 1.5, [2_000, 4_000, 6_000, 10_000], sensitivity, specificity, h2_effect)
    for units in (1_000, 2_000):
        rows.append({"variant": "H2-S2", "scenario": f"health {non_specialist:.2f} vs control {CONTROL_NON_SPECIALIST}", "test": "two shares",
                     "share": non_specialist, "design_effect": h2_effect, "units": units,
                     "power": power.two_share_power(non_specialist, CONTROL_NON_SPECIALIST, units, units, h2_effect)})
    for ratio in (1.25, 1.5, 2.0):
        rows.append({"variant": "H2-S3", "scenario": f"hazard ratio {ratio}", "test": "Cox", "share": non_specialist,
                     "units_needed": power.events_needed(non_specialist, ratio)})
    for name, share in (("alternative by owner", values["h2_alt_owner_share"]), ("alternative by domain", values["h2_alt_domain_share"])):
        for units in (1_500, 4_000):
            rows.append({"variant": "H2-S4", "scenario": f"{name} below {MARGINAL_SHARE}", "test": "bound", "share": share,
                         "design_effect": h2_effect, "units": units, "power": power.bound_power(units, share, MARGINAL_SHARE, h2_effect)})
    for share in (0.5, 0.8):
        for units in (20, 30):
            rows.append({"variant": "H2-S5", "scenario": f"institutional share {share} vs 0.25", "test": "binomial", "share": share,
                         "units": units, "power": power.binomial_power(units, share, 0.25)})
    return pd.DataFrame(rows)


def check() -> None:
    """The planning formula against the simulation (one group, no fixed effects)."""
    for share, units, sensitivity, specificity in ((0.15, 10_000, 1.0, 1.0), (0.10, 30_000, 0.6, 0.97)):
        slope = np.log(1.25) / 13
        simulated = power.simulate(1, 14, units // 14, share, float(np.exp(slope)), intercept_sd=0.0, replicates=200,
                                   fixed_effects=False, sensitivity=sensitivity, specificity=specificity)["power"]
        print(f"share {share}, units {units}, Se {sensitivity}, Sp {specificity}: simulation {simulated:.3f}, "
              f"formula {power.trend_power(units, share, slope, 14, sensitivity, specificity):.3f}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replicates", type=int, default=200)
    parser.add_argument("--plan", action="store_true", help="also write the planning grid of the step-by-step plan")
    parser.add_argument("--check", action="store_true", help="compare the planning formula with the simulation")
    args = parser.parse_args()
    if args.check:
        check()
        return
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

    if args.plan:
        values = planning_values()
        (HYPOTHESES_V2_DIR / "power_plan_values.json").write_text(json.dumps(values, indent=2), encoding="utf-8")
        plan = plan_table(values)
        plan.to_csv(HYPOTHESES_V2_DIR / "power_plan.csv", index=False, encoding="utf-8")
        print(json.dumps(values, indent=1))
        print(plan.drop_duplicates(["variant", "scenario", "design_effect"])[
            ["variant", "scenario", "share", "design_effect", "units_needed", "units_needed_equivalence"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
