"""Test the preregistered hypotheses H1 and H2 (docs/hipotezy.md); write tables and plots to annotations/hypotheses/.

`--confirmatory` marks the reported run. It refuses while the preregistration
(docs/hipotezy.md, config.yaml, codebook/domains.yaml, this script and the
analysis modules) is uncommitted. H1-A also needs stance labels of the H1
sample from a tuned stance_v1 that has run on the test split (07b). Without
`--confirmatory` every result is marked exploratory.
"""

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime

import pandas as pd

from digital_media_analysis import annotations, hypotheses, wikipedia_refs
from digital_media_analysis.config_reader import get_hypotheses
from digital_media_analysis.instruments import stance_v1
from digital_media_analysis.paths import FRAME_LABELS_DIR, HYPOTHESES_DIR, PREDICTIONS_DIR, PROJECT_ROOT, VALIDATION_DIR

PREREGISTRATION = [
    "docs/hipotezy.md", "config.yaml", "codebook/domains.yaml", "scripts/09_test_hypotheses.py",
    "src/digital_media_analysis/hypotheses.py", "src/digital_media_analysis/wikipedia_refs.py",
]
HYPOTHESES = ["h1a", "h1b", "h2"]


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True, check=True).stdout.strip()


def h1_frame(sample: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    return sample.merge(labels, on="unit_id").reset_index(drop=True)


def gold_error_rates(codes: list[str]) -> dict:
    """Sensitivity and specificity of gliner_v1 for a group of categories on the Reddit gold test split."""
    path = PREDICTIONS_DIR / "gliner_v1_test.csv"
    if not path.exists():
        return {"sensitivity": float("nan"), "specificity": float("nan"), "positives": 0, "negatives": 0}
    reference, _ = annotations.gold_reference(annotations.load_labels("gold"))
    predicted = pd.read_csv(path, dtype={"unit_id": str})
    paired = reference.merge(predicted, on=["unit_id", "platform"], suffixes=("", "_pred"))
    paired = paired[paired["platform"].eq("reddit")]
    return hypotheses.error_rates(hypotheses.has_any(paired["source_types"], codes), hypotheses.has_any(paired["source_types_pred"], codes))


def run_trends(frame: pd.DataFrame, hypothesis: str, specs: list[tuple[str, str]], fixed_effect: str, cluster: str,
               periods: dict[str, list[int]], extra: dict[str, pd.DataFrame] | None = None) -> list[dict]:
    rows = []
    analyses = {name: hypotheses.in_years(frame, period) for name, period in periods.items()}
    analyses.update(extra or {})
    for analysis, data in analyses.items():
        start = int(data["year"].min()) if len(data) else 0
        for outcome, direction in specs:
            rows.append({"hypothesis": hypothesis, "analysis": analysis,
                         **hypotheses.trend(data, outcome, fixed_effect, cluster, direction, start)})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hypotheses", nargs="+", choices=HYPOTHESES, default=HYPOTHESES)
    parser.add_argument("--confirmatory", action="store_true", help="The reported run: preregistration must be committed.")
    parser.add_argument("--samples", type=int, default=hypotheses.BOOTSTRAP_SAMPLES, help="Bootstrap replicates.")
    args = parser.parse_args()
    head, dirty = git("rev-parse", "HEAD"), git("status", "--porcelain", "--", *PREREGISTRATION)
    if args.confirmatory and dirty:
        sys.exit(f"Commit the preregistration before the confirmatory run:\n{dirty}")
    mode = "confirmatory" if args.confirmatory else "exploratory"
    settings = get_hypotheses()
    h1, h2 = settings["h1"], settings["h2"]
    trends, yearly, notes = [], [], {}

    if {"h1a", "h1b"} & set(args.hypotheses):
        sample = pd.read_csv(HYPOTHESES_DIR / "h1_sample.csv", dtype={"unit_id": str})
        periods = {"primary": h1["period"], "sensitivity_period": h1["sensitivity_period"]}
        if "h1b" in args.hypotheses:
            labels = pd.read_csv(FRAME_LABELS_DIR / "h1_gliner_v1.csv", dtype={"unit_id": str})
            frame = hypotheses.h1b_outcomes(h1_frame(sample, labels), h1["consensus_sources"], h1["alternative_sources"])
            frame = frame.reset_index(drop=True)
            specs = [("consensus", "decrease"), ("alternative", "increase")]
            per_subreddit = {f"only_{name}": hypotheses.in_years(frame[frame["group"].eq(name)], h1["period"])
                             for name in ["science", "conspiracy"]}
            trends += run_trends(frame, "H1-B", specs, "group", "day", periods, per_subreddit)
            primary = hypotheses.in_years(frame, h1["period"]).reset_index(drop=True)
            for outcome, _ in specs:
                shares = hypotheses.yearly_shares(primary, outcome, strata=["group", "year"], samples=args.samples)
                rates = gold_error_rates(h1["consensus_sources"] if outcome == "consensus" else h1["alternative_sources"])
                shares = shares.assign(
                    corrected=shares["share"].map(lambda p: hypotheses.rogan_gladen(p, rates["sensitivity"], rates["specificity"])),
                    gold_positives=rates["positives"],
                )
                by_group = hypotheses.yearly_shares(primary, outcome, by=["group"], strata=["group", "year"], samples=args.samples)
                yearly += [shares.assign(hypothesis="H1-B", outcome=outcome, group="all"),
                           by_group.assign(hypothesis="H1-B", outcome=outcome)]
        if "h1a" in args.hypotheses:
            path = FRAME_LABELS_DIR / "h1_stance_v1.csv"
            tested = (VALIDATION_DIR / "stance_test_run.json").exists()
            if not (stance_v1.TUNED and path.exists() and tested):
                notes["H1-A"] = "czeka na etykiety stanowiska: strojenie stance_v1 na dev, test (07b) i etykiety próby (08)"
            else:
                stances = pd.read_csv(path, dtype={"unit_id": str})
                frame = hypotheses.h1a_outcomes(h1_frame(sample, stances)).reset_index(drop=True)
                specs = [("challenges", "increase"), ("supports", "decrease")]
                per_subreddit = {f"only_{name}": hypotheses.in_years(frame[frame["group"].eq(name)], h1["period"])
                                 for name in ["science", "conspiracy"]}
                trends += run_trends(frame, "H1-A", specs, "group", "day", periods, per_subreddit)
                primary = hypotheses.in_years(frame, h1["period"]).reset_index(drop=True)
                for outcome, _ in specs:
                    yearly.append(hypotheses.yearly_shares(primary, outcome, strata=["group", "year"], samples=args.samples)
                                  .assign(hypothesis="H1-A", outcome=outcome, group="all"))

    if "h2" in args.hypotheses:
        links = wikipedia_refs.load_added_links()
        frame = hypotheses.h2_outcomes(links, h2["period"], h2["alternative_categories"]).reset_index(drop=True)
        extra = {
            "without_covid19": frame[frame["page"].ne("COVID-19")],
            "without_2020": frame[frame["year"].ne(2020)],
            "classified_only": frame[frame["category"].ne(wikipedia_refs.UNCLASSIFIED)],
        }
        trends += run_trends(frame, "H2", [("alternative", "increase")], "page", "revision", {"primary": h2["period"]}, extra)
        yearly.append(hypotheses.yearly_shares(frame, "alternative", strata=["year"], samples=args.samples)
                      .assign(hypothesis="H2", outcome="alternative", group="all"))
        notes["H2 unclassified links"] = int(frame["category"].eq(wikipedia_refs.UNCLASSIFIED).sum())

    HYPOTHESES_DIR.mkdir(parents=True, exist_ok=True)
    table = pd.DataFrame(trends)
    if len(table):
        table["supported"] = table["p_one_sided"] < settings["alpha"]
        table = table.assign(mode=mode)
        table.to_csv(HYPOTHESES_DIR / f"{mode}_trends.csv", index=False, encoding="utf-8")
    if yearly:
        pd.concat(yearly, ignore_index=True).assign(mode=mode).to_csv(HYPOTHESES_DIR / f"{mode}_yearly.csv", index=False, encoding="utf-8")
    (HYPOTHESES_DIR / f"{mode}_run.json").write_text(json.dumps({
        "mode": mode, "created_utc": datetime.now(UTC).isoformat(timespec="seconds"), "commit": head,
        "uncommitted_preregistration": bool(dirty), "hypotheses": args.hypotheses, "settings": settings, "notes": notes,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Mode: {mode}")
    for row in table[table["analysis"].eq("primary")].itertuples(index=False) if len(table) else []:
        print(f"{row.hypothesis:<5} {row.outcome:<12} {row.direction:<8} OR/rok {row.odds_ratio_per_year:.3f} "
              f"[{row.ci_low:.3f}, {row.ci_high:.3f}] p={row.p_one_sided:.4f} n={row.units} {row.note}")
    for key, value in notes.items():
        print(f"{key}: {value}")
    print(f"Tables written to {HYPOTHESES_DIR}")


if __name__ == "__main__":
    main()
