"""Power gate of the v2 confirmatory run (docs/plan_poprawy_krok_po_kroku.md, step 7; change 1 of docs/hipotezy_v2.md).

Default: the nuisance values of every variant of the hypothesis ladders from the v2 files (no trend is estimated:
units after the exclusions, the stance instrument's sensitivity and specificity on the validation test, the pooled
base shares, the design effects of days and revisions computed without the year), the power of each variant, and the
choice of the primary test of each family. Writes annotations/hypotheses_v2/power_gate.json once; scripts/16 refuses
the confirmatory run until that file is committed. `--force` redraws it, before the confirmatory run only.
`--plan` runs the same gate on the planning values of scripts/17 (power_plan_values.json) and assumed units, to show
what the gate would pick; it writes power_gate_plan.json, which the confirmatory run never reads.
"""

import argparse
import json
from datetime import UTC, datetime

import numpy as np
import pandas as pd

from digital_media_analysis import hypotheses, ladders, power, wikipedia_refs
from digital_media_analysis.config_reader import get_hypotheses_v2, get_wikipedia_pages
from digital_media_analysis.datasets import page_title
from digital_media_analysis.owners import UNCODED
from digital_media_analysis.paths import (
    FRAME_LABELS_DIR,
    HYPOTHESES_DIR,
    HYPOTHESES_V2_DIR,
    PROJECT_ROOT,
)
from digital_media_analysis.prereg import git

GATE_PATH = HYPOTHESES_V2_DIR / "power_gate.json"
PLAN_PATH = HYPOTHESES_V2_DIR / "power_gate_plan.json"
UNCODED_LIMIT = 0.05  # v2: more uncoded platform links than this makes the owner-based verdict depend on two bounds


def gliner_alternative_errors() -> dict:
    """Sensitivity, specificity and validity (Youden's J above 0.2) of gliner_v1's alternative sources (v1 audit)."""
    audit = pd.read_csv(HYPOTHESES_DIR / "audit_error_rates.csv")
    row = audit[audit["source"].eq("pooled") & audit["indicator"].eq("alternative")].iloc[0]
    return {"sensitivity": float(row["sensitivity"]), "specificity": float(row["specificity"]), "valid": bool(row["valid"])}


def h1_frames(settings: dict) -> dict[str, pd.DataFrame]:
    """The H1 sample without v1 posts, its relevant units (stance) and citing units (gliner_v1), whichever exist."""
    rules = settings["ladders"]
    sample = pd.read_csv(HYPOTHESES_V2_DIR / "h1_sample.csv", dtype={"unit_id": str, "post_id": str})
    if rules["exclude_v1_units"]:
        sample = ladders.without_v1_posts(sample, ladders.v1_post_ids(PROJECT_ROOT / folder for folder in rules["v1_reddit_frames"]))
    questioning = {name.lower() for name in rules["h1"]["questioning_subreddits"]}
    frames = {"units": sample.assign(questioning=sample["group"].str.lower().isin(questioning).astype(int))}
    stance_path = FRAME_LABELS_DIR / "h1v2_stance_v2.csv"
    if stance_path.exists():
        stance = sample.merge(pd.read_csv(stance_path, dtype={"unit_id": str}), on="unit_id")
        relevant = stance[stance["consensus_stance"].ne("not_applicable")]
        frames["relevant"] = relevant.assign(challenges=relevant["consensus_stance"].eq("challenges").astype(int))
    sources_path = FRAME_LABELS_DIR / "h1v2_gliner_v1.csv"
    if sources_path.exists():
        labels = pd.read_csv(sources_path, dtype={"unit_id": str})
        citing = sample.merge(labels[labels["cites_source"].astype(int).eq(1)][["unit_id", "source_types"]], on="unit_id")
        frames["citing"] = citing.assign(alternative=hypotheses.has_any(citing["source_types"], rules["h1"]["alternative_sources"]))
    return frames


def h2_frames(settings: dict) -> dict[str, pd.DataFrame]:
    """First additions to articles in the H2 period without v1 pages and bulk revisions, by group."""
    rules, h2 = settings["ladders"], settings["h2"]
    links = pd.read_csv(HYPOTHESES_V2_DIR / "h2_links.csv", dtype={"url": str})
    articles = links[links["ns"].eq(0)]
    articles = ladders.without_bulk(articles, int(rules["h2"]["bulk_revision_links"]))
    if rules["exclude_v1_units"]:
        articles = ladders.without_pages(articles, [page_title(url) for url in get_wikipedia_pages()])
    first = articles[articles["year"].between(*h2["period"]) & articles["first_addition"]]
    classified = first[first["category"].ne(wikipedia_refs.UNCLASSIFIED)]
    classified = classified.assign(non_specialist=classified["category"].isin(rules["h2"]["non_specialist_categories"]).astype(int))
    return {"main": first[first["group"].eq("health")], "classified": classified[classified["group"].eq("health")],
            "control": classified[classified["group"].eq("control")]}


def trend_spec(frame: pd.DataFrame, outcome: str, cluster: str, years: int, sesoi: float, weight: str | None = None, **extra) -> dict:
    share = float(np.average(frame[outcome], weights=frame[weight]) if weight else frame[outcome].mean())
    return {"test": "trend", "units": len(frame), "share": share, "years": years, "sesoi_period_odds_ratio": sesoi,
            "design_effect": power.design_effect(frame[outcome], frame[cluster])["design_effect"], **extra}


def specs_from_data(settings: dict) -> dict[str, dict]:
    """Nuisance values of every variant from the v2 files; variants without data stay invalid."""
    specs: dict[str, dict] = {}
    h1, h2, rules = settings["h1"], settings["h2"], settings["ladders"]
    if (HYPOTHESES_V2_DIR / "h1_sample.csv").exists():
        frames, years = h1_frames(settings), h1["period"][1] - h1["period"][0] + 1
        test_path = HYPOTHESES_V2_DIR / "h1_instrument_test.json"
        if "relevant" in frames and test_path.exists():
            test = json.loads(test_path.read_text(encoding="utf-8"))
            counts = test["challenges_counts"]["all"]
            sensitivity = counts["tp"] / max(counts["tp"] + counts["fn"], 1)
            specificity = counts["tn"] / max(counts["tn"] + counts["fp"], 1)
            gate = rules["h1"]["stance_gate"]
            valid = bool(test["gate_passed"]) and sensitivity >= gate["sensitivity"] and specificity >= gate["specificity"]
            spec = trend_spec(frames["relevant"], "challenges", "day", years, h1["sesoi_period_odds_ratio"],
                              sensitivity=sensitivity, specificity=specificity, valid=valid,
                              reason="" if valid else "stance_v2 poniżej bramki B6 (F1, kappa, czułość, swoistość)")
            # Base share from the reference of the validation test, pooled over periods.
            specs["H1"] = spec | {"share": (counts["tp"] + counts["fn"]) / max(sum(counts.values()), 1)}
        if "citing" in frames:
            errors = gliner_alternative_errors()
            seen = float(frames["citing"]["alternative"].mean())
            true = float(np.clip(hypotheses.rogan_gladen(seen, errors["sensitivity"], errors["specificity"]), 0.001, 0.999))
            for name, weight in (("H1-S1", None), ("H1-S2", "weight")):
                specs[name] = trend_spec(frames["citing"], "alternative", "day", years, h1["sesoi_period_odds_ratio"], weight,
                                         sensitivity=errors["sensitivity"], specificity=errors["specificity"], valid=errors["valid"],
                                         reason="" if errors["valid"] else "audyt źródeł alternatywnych nieważny (J ≤ 0,2)") | {"share": true}
        specs["H1-S3"] = trend_spec(frames["units"], "questioning", "day", years, h1["sesoi_period_odds_ratio"], "weight", valid=True)
    if (HYPOTHESES_V2_DIR / "h2_links.csv").exists():
        frames, years = h2_frames(settings), h2["period"][1] - h2["period"][0] + 1
        main, classified, control = frames["main"], frames["classified"], frames["control"]
        platform = main[main["platform"].fillna("").ne("")]
        uncoded = float(platform["uncoded_owner"].mean()) if len(platform) else 0.0
        coded = uncoded <= UNCODED_LIMIT
        reason = "" if coded else f"{uncoded:.1%} linków do platform bez kodu właściciela"
        specs["H2"] = trend_spec(main, "alt_owner", "revid", years, h2["sesoi_period_odds_ratio"], valid=coded, reason=reason)
        specs["H2-S1"] = trend_spec(classified, "non_specialist", "revid", years, h2["sesoi_period_odds_ratio"], valid=True)
        both = pd.concat([classified, control])
        specs["H2-S2"] = {"test": "two_shares", "valid": len(control) > 0, "share": float(both["non_specialist"].mean()),
                          "units_first": len(classified), "units_second": len(control), "sesoi_odds_ratio": rules["h2"]["group_sesoi_odds_ratio"],
                          "design_effect": power.design_effect(both["non_specialist"], both["article"])["design_effect"]}
        specs["H2-S4"] = {"test": "bound", "valid": coded, "reason": reason, "units": len(main),
                          "planning_share": rules["h2"]["planning_alternative_share"], "bound": rules["h2"]["marginal_share"],
                          "design_effect": power.design_effect(main["alt_owner"], main["article"])["design_effect"]}
        specs["H2-S3"] = {"test": "cox", "valid": True, "events": int((~classified["censored"].astype(bool)).sum()),
                          "exposed_share": float(classified["non_specialist"].mean()), "hazard_ratio": rules["h2"]["survival_hazard_ratio"]}
        owned = main[main["alt_domain"].eq(1) & ~main["owner_type"].fillna("").isin(["", UNCODED])]
        specs["H2-S5"] = {"test": "binomial", "valid": len(owned) > 0, "units": len(owned),
                          "planning_share": rules["h2"]["planning_institution_share"], "null_share": rules["h2"]["institution_null_share"]}
    return specs


def specs_from_plan(settings: dict, units: dict[str, int]) -> dict[str, dict]:
    """The same variants from the planning values of scripts/17 and assumed units (illustration only)."""
    values = json.loads((HYPOTHESES_V2_DIR / "power_plan_values.json").read_text(encoding="utf-8"))
    h1, h2, rules = settings["h1"], settings["h2"], settings["ladders"]
    deff_h1, deff_h2 = values["h1_implied_design_effect"], values["h2_design_effect"]["without_bulk_revisions"]["design_effect"]
    trend = {"test": "trend", "valid": True}
    gliner = {"sensitivity": values["h1_gliner_alternative_sensitivity"], "specificity": values["h1_gliner_alternative_specificity"]}
    return {
        "H1": trend | {"units": units["h1_relevant"], "share": 0.10, "sensitivity": 0.7, "specificity": 0.98, "design_effect": deff_h1,
                       "years": 14, "sesoi_period_odds_ratio": h1["sesoi_period_odds_ratio"]},
        "H1-S1": trend | gliner | {"units": units["h1_citing"], "share": values["h1_alternative_true_share"], "design_effect": deff_h1,
                                   "years": 14, "sesoi_period_odds_ratio": h1["sesoi_period_odds_ratio"]},
        "H1-S2": trend | gliner | {"units": units["h1_citing"], "share": values["h1_alternative_true_share"], "design_effect": deff_h1,
                                   "years": 14, "sesoi_period_odds_ratio": h1["sesoi_period_odds_ratio"]},
        "H1-S3": trend | {"units": units["h1_units"], "share": 0.10, "design_effect": 1.5, "years": 14,
                          "sesoi_period_odds_ratio": h1["sesoi_period_odds_ratio"]},
        "H2": trend | {"units": units["h2_links"], "share": values["h2_alt_owner_share"], "design_effect": deff_h2, "years": 7,
                       "sesoi_period_odds_ratio": h2["sesoi_period_odds_ratio"]},
        "H2-S1": trend | {"units": units["h2_links"], "share": values["h2_non_specialist_share_without_bulk"], "design_effect": deff_h2,
                          "years": 7, "sesoi_period_odds_ratio": h2["sesoi_period_odds_ratio"]},
        "H2-S2": {"test": "two_shares", "valid": True, "share": values["h2_non_specialist_share_without_bulk"], "units_first": units["h2_links"],
                  "units_second": units["h2_links"], "sesoi_odds_ratio": rules["h2"]["group_sesoi_odds_ratio"], "design_effect": deff_h2},
        "H2-S4": {"test": "bound", "valid": True, "units": units["h2_links"], "planning_share": rules["h2"]["planning_alternative_share"],
                  "bound": rules["h2"]["marginal_share"], "design_effect": deff_h2},
        "H2-S3": {"test": "cox", "valid": True, "events": units["h2_removals"], "exposed_share": values["h2_non_specialist_share_without_bulk"],
                  "hazard_ratio": rules["h2"]["survival_hazard_ratio"]},
        "H2-S5": {"test": "binomial", "valid": True, "units": units["h2_alt_domain_owned"],
                  "planning_share": rules["h2"]["planning_institution_share"], "null_share": rules["h2"]["institution_null_share"]},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true", help="Run the gate on planning values and assumed units (illustration).")
    parser.add_argument("--force", action="store_true", help="Redraw power_gate.json (only before the confirmatory run).")
    parser.add_argument("--h1-relevant", type=int, default=50_000, help="--plan: units with a stance")
    parser.add_argument("--h1-citing", type=int, default=50_000, help="--plan: units citing a source")
    parser.add_argument("--h1-units", type=int, default=60_000, help="--plan: all sample units")
    parser.add_argument("--h2-links", type=int, default=4_000, help="--plan: first additions per group after exclusions")
    parser.add_argument("--h2-removals", type=int, default=600, help="--plan: removed links")
    parser.add_argument("--h2-alt-domain-owned", type=int, default=30, help="--plan: alternative-by-domain links with a coded owner")
    args = parser.parse_args()
    settings = get_hypotheses_v2()
    target = settings["ladders"]["target_power"]
    if args.plan:
        units = {"h1_relevant": args.h1_relevant, "h1_citing": args.h1_citing, "h1_units": args.h1_units, "h2_links": args.h2_links,
                 "h2_removals": args.h2_removals, "h2_alt_domain_owned": args.h2_alt_domain_owned}
        specs, path, source = specs_from_plan(settings, units), PLAN_PATH, "planning values (illustration, not for the confirmatory run)"
    else:
        if GATE_PATH.exists() and not args.force:
            raise SystemExit(f"{GATE_PATH} exists: the gate is drawn once, before the confirmatory run (use --force only before it).")
        if (HYPOTHESES_V2_DIR / "confirmatory_run.json").exists():
            raise SystemExit("The confirmatory run exists: the power gate cannot be redrawn after it.")
        specs, path, source = specs_from_data(settings), GATE_PATH, "v2 data (nuisance values only, no trend)"
    decision = ladders.gate(specs, target)
    record = {"created_utc": datetime.now(UTC).isoformat(timespec="seconds"), "commit": git("rev-parse", "HEAD"), "source": source,
              "target_power": target, "inputs": specs, "decision": decision}
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False, default=float) + "\n", encoding="utf-8")
    for family, item in decision.items():
        print(f"{family}: primary {item['primary']}, secondary {item['secondary']}, descriptive {item['descriptive']}")
        for name, variant in item["variants"].items():
            powers = (f"power {variant['power']:.2f}" if variant["power"] is not None else "no power") + (
                f", TOST {variant['power_equivalence']:.2f}" if variant.get("power_equivalence") is not None else "")
            print(f"  {name}: {powers}{'' if variant['valid'] else ' (invalid: ' + variant.get('reason', '') + ')'}")
    print(f"-> {path}")


if __name__ == "__main__":
    main()
