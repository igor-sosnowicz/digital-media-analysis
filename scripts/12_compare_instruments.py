"""Material for slide 4 (instrument analysis) and the gold estimate of the source shares.

From saved predictions and labels only (nothing is run on the test split here). Writes to annotations/validation/:
- comparison_kappa.csv: Cohen's kappa of each instrument against gold on the test
  split next to the kappa between annotators in the pilot (`cites_source`,
  `edit_about_sources`);
- comparison_mcnemar.csv: exact McNemar test of every pair of instruments on
  `cites_source`, test split, per platform;
- comparison_shares.csv and comparison_rankings.csv: weighted category shares on
  the test split from gold and from each instrument, and Kendall's tau between
  each instrument's ranking of the categories and the gold one;
- gold_shares.csv: weighted shares of citing units and of each category from the
  gold labels of dev and test together, the first estimate that needs no instrument.
"""

import argparse
from itertools import combinations

import pandas as pd

from digital_media_analysis import adjudication, annotations, gold, validation
from digital_media_analysis.codebook import load_codebook
from digital_media_analysis.instruments import runner
from digital_media_analysis.paths import AGREEMENT_DIR, PREDICTIONS_DIR, VALIDATION_DIR

SPLIT = "test"
VARIABLES = ["cites_source", "edit_about_sources"]


def load_predictions(split: str) -> dict[str, pd.DataFrame]:
    found = {}
    for instrument in runner.INSTRUMENTS:
        path = PREDICTIONS_DIR / f"{instrument}_{split}.csv"
        if path.exists():
            found[instrument] = pd.read_csv(path, dtype={"unit_id": str, "source_types": str}).astype(
                {"cites_source": "Int64", "edit_about_sources": "Int64"}
            )
    return found


def kappa_table(metrics: pd.DataFrame, agreement: pd.DataFrame | None) -> pd.DataFrame:
    rows = []
    if agreement is not None:
        for row in agreement[agreement["variable"].isin(VARIABLES)].itertuples(index=False):
            rows.append({"platform": row.platform, "variable": row.variable, "rater": "annotators (pilot)",
                         "kappa": row.kappa, "low": row.kappa_low, "high": row.kappa_high, "units": row.units,
                         "agreement": row.observed_agreement, "prevalence": row.prevalence})
    chosen = metrics[metrics["subset"].eq("all") & metrics["variable"].isin(VARIABLES)]
    for (instrument, platform, variable), part in chosen.groupby(["instrument", "platform", "variable"]):
        values = part.set_index("metric")
        rows.append({"platform": platform, "variable": variable, "rater": instrument,
                     "kappa": values.loc["kappa", "value"], "low": values.loc["kappa", "low"], "high": values.loc["kappa", "high"],
                     "units": values.loc["kappa", "units"], "agreement": values.loc["accuracy", "value"], "prevalence": float("nan")})
    return pd.DataFrame(rows).sort_values(["platform", "variable", "rater"], ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=validation.BOOTSTRAP_SAMPLES, help="Bootstrap replicates.")
    args = parser.parse_args()

    codes = [code for code in load_codebook().category_codes if code != "none"]
    manifest = gold.load_manifest()
    reference, _ = annotations.gold_reference(annotations.load_labels("gold"), adjudication.load_decisions("gold"))
    reference = reference.merge(manifest[["unit_id", "platform", "split"]], on=["unit_id", "platform"])
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

    shares = validation.weighted_shares(reference[reference["split"].isin(["dev", "test"])], manifest, codes, samples=args.samples)
    shares.to_csv(VALIDATION_DIR / "gold_shares.csv", index=False, encoding="utf-8")
    for row in shares[shares["variable"].eq("cites_source")].itertuples(index=False):
        print(f"gold {row.platform:<10} cites_source share {row.share:.2f} [{row.low:.2f}, {row.high:.2f}] (n = {row.units})")

    metrics_path = VALIDATION_DIR / f"{SPLIT}_metrics.csv"
    agreement_path = AGREEMENT_DIR / "pilot_agreement.csv"
    if metrics_path.exists():
        agreement = pd.read_csv(agreement_path) if agreement_path.exists() else None
        kappa = kappa_table(pd.read_csv(metrics_path), agreement)
        kappa.to_csv(VALIDATION_DIR / "comparison_kappa.csv", index=False, encoding="utf-8")
        for row in kappa.itertuples(index=False):
            print(f"kappa {row.platform:<10} {row.variable:<19} {row.rater:<20} {row.kappa:.2f} [{row.low:.2f}, {row.high:.2f}]")

    predictions = load_predictions(SPLIT)
    test_reference = reference[reference["split"].eq(SPLIT)].drop(columns="split")
    pairs = []
    for first, second in combinations(predictions, 2):
        both = test_reference.merge(predictions[first], on=["unit_id", "platform"], suffixes=("", "_first"))
        both = both.merge(predictions[second][["unit_id", "platform", "cites_source"]].rename(columns={"cites_source": "cites_source_second"}),
                          on=["unit_id", "platform"])
        for platform, part in both.groupby("platform"):
            result = validation.mcnemar(part, "cites_source_first", "cites_source_second")
            if result["units"]:
                pairs.append({"platform": platform, "first": first, "second": second, **result})
    pd.DataFrame(pairs).to_csv(VALIDATION_DIR / "comparison_mcnemar.csv", index=False, encoding="utf-8")
    for row in pairs:
        print(f"McNemar {row['platform']:<10} {row['first']} vs {row['second']}: {row['only_first_right']} vs "
              f"{row['only_second_right']} discordant, p = {row['p_exact']:.3f}")

    sources = {"gold": test_reference}
    for instrument, labels in predictions.items():
        labels = labels.merge(test_reference[["unit_id", "platform"]], on=["unit_id", "platform"])
        if labels["source_types"].notna().any():
            sources[instrument] = labels
    split_shares = pd.concat(
        [validation.weighted_shares(labels, manifest, codes, samples=0).assign(source=source) for source, labels in sources.items()],
        ignore_index=True,
    )
    split_shares.to_csv(VALIDATION_DIR / "comparison_shares.csv", index=False, encoding="utf-8")
    rankings = validation.ranking_agreement(split_shares[split_shares["variable"].ne("cites_source")])
    rankings.to_csv(VALIDATION_DIR / "comparison_rankings.csv", index=False, encoding="utf-8")
    for row in rankings.itertuples(index=False):
        print(f"ranking {row.platform:<10} {row.source:<12} tau {row.kendall_tau:.2f} same top category: {row.same_top_category}")
    print(f"Comparison tables -> {VALIDATION_DIR}")


if __name__ == "__main__":
    main()
