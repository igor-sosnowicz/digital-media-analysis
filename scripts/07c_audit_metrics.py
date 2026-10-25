"""Audit of the H1-B source indicators: import the audit workbooks and estimate gliner_v1's error rates.

Reads annotations/sheets/audit_<annotator>.xlsx (rows without labels are
skipped), saves the labels text-free to annotations/labels/audit/, measures
agreement when two people coded, and takes the agreed labels (or the arbiter's,
scripts/05b_adjudicate.py --phase audit) as reference. Writes to annotations/hypotheses/:
- audit_error_rates.csv: sensitivity, specificity and Youden's J per indicator,
  from the audit, the Reddit gold test split and both pooled, with the validity
  gate of the preregistration (J > 0.2);
- audit_corrected_yearly.csv: the H1-B yearly shares of the confirmatory run
  corrected by Rogan-Gladen with the pooled and the audit-only rates.
No hypothesis is tested here (docs/hipotezy.md, amendments of 25.10.2026).
"""

import argparse
import sys

import pandas as pd

from digital_media_analysis import adjudication, agreement, annotations, audit, gold
from digital_media_analysis.annotation_sheets import read_workbook
from digital_media_analysis.codebook import load_codebook
from digital_media_analysis.config_reader import get_hypotheses
from digital_media_analysis.paths import AGREEMENT_DIR, HYPOTHESES_DIR, PREDICTIONS_DIR

PHASE = "audit"


def import_audit(sample: pd.DataFrame) -> pd.DataFrame:
    """Labels of every audit workbook; stops on problems, as the gold import does."""
    codebook = load_codebook()
    expected = set(sample["unit_id"].astype(str))
    failed = False
    for annotator, path in annotations.workbook_paths(PHASE).items():
        labels, problems = read_workbook(path, codebook, partial=True)
        if unexpected := sorted(set(labels["unit_id"]) - expected):
            problems.append(f"{len(unexpected)} jednostek spoza próby audytu, np. {unexpected[:3]}")
        if repeated := sorted(labels.loc[labels["unit_id"].duplicated(), "unit_id"].unique()):
            problems.append(f"powtórzone unit_id {repeated}")
        if mismatched := sorted(set(labels["annotator"].astype(str)) - {annotator}):
            problems.append(f"kolumna annotator zawiera {mismatched}, a plik należy do {annotator!r}")
        if problems:
            failed = True
            print(f"{path.name}: {len(problems)} problem(s)")
            for problem in problems[:20]:
                print(f"  - {problem}")
            continue
        if labels.empty:
            print(f"{path.name}: no labels yet")
            continue
        annotations.save_labels(labels, annotations.label_path(PHASE, annotator))
        print(f"{path.name}: {len(labels)} labels -> {annotations.label_path(PHASE, annotator)}")
    if failed:
        sys.exit("Fix the problems above in the audit workbooks and run again.")
    return annotations.load_labels(PHASE)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=audit.BOOTSTRAP_SAMPLES, help="Bootstrap replicates.")
    args = parser.parse_args()

    sample = pd.read_csv(HYPOTHESES_DIR / "h1_audit_sample.csv", dtype={"unit_id": str})
    labels = import_audit(sample)
    if labels.empty:
        sys.exit("No audit labels yet: code annotations/sheets/audit_<annotator>.xlsx first.")
    if labels["annotator"].nunique() >= 2:
        table = agreement.agreement_table(labels, load_codebook().category_codes)
        AGREEMENT_DIR.mkdir(parents=True, exist_ok=True)
        table.to_csv(AGREEMENT_DIR / "audit_agreement.csv", index=False, encoding="utf-8")
        headline = table[table["variable"].isin(["cites_source", "source_types"])]
        for row in headline.itertuples(index=False):
            print(f"agreement {row.variable:<14} n={row.units:<4} alpha={row.alpha:.3f} [{row.alpha_low:.3f}, {row.alpha_high:.3f}]")
    reference, conflicts = annotations.gold_reference(labels, adjudication.load_decisions(PHASE))
    if len(conflicts):
        print(f"{conflicts['unit_id'].nunique()} audited posts coded differently wait for the arbiter (scripts/05b_adjudicate.py --phase audit).")

    h1 = get_hypotheses()["h1"]
    indicators = {"consensus": h1["consensus_sources"], "alternative": h1["alternative_sources"]}
    frames = {"audit": audit.audit_frame(sample, reference)}
    predictions = PREDICTIONS_DIR / "gliner_v1_test.csv"
    if predictions.exists():
        gold_reference, _ = annotations.gold_reference(annotations.load_labels("gold"), adjudication.load_decisions("gold"))
        frames["gold_test"] = audit.gold_frame(gold_reference, pd.read_csv(predictions, dtype={"unit_id": str}), gold.load_manifest())
    frames["pooled"] = audit.pooled(list(frames.values()))
    table = audit.rate_table(frames, indicators, samples=args.samples)
    table.to_csv(HYPOTHESES_DIR / "audit_error_rates.csv", index=False, encoding="utf-8")
    for row in table.itertuples(index=False):
        print(f"{row.source:<10} {row.indicator:<12} sens {row.sensitivity:.2f} spec {row.specificity:.2f} "
              f"J {row.youden:.2f} [{row.youden_low:.2f}, {row.youden_high:.2f}] posts={row.posts} positives={row.positives} "
              f"{'valid' if row.valid else 'descriptive only (J <= 0.2)'}")

    audited = table[table["source"].eq("audit") & table["indicator"].eq("consensus")]
    if len(audited) and audited["positives"].iloc[0] < audit.MIN_AUDIT_POSITIVES:
        print(f"Fewer than {audit.MIN_AUDIT_POSITIVES} audited posts with a consensus source: "
              "the validity gate counts as not met (docs/hipotezy.md, 25.10.2026, point 5).")

    yearly_path = HYPOTHESES_DIR / "confirmatory_yearly.csv"
    if yearly_path.exists():
        yearly = pd.read_csv(yearly_path)
        yearly = yearly[yearly["group"].eq("all")]
        corrected = pd.concat([audit.corrected_shares(yearly, table, source) for source in ["pooled", "audit"]], ignore_index=True)
        corrected.to_csv(HYPOTHESES_DIR / "audit_corrected_yearly.csv", index=False, encoding="utf-8")
        print(f"Corrected yearly shares -> {HYPOTHESES_DIR / 'audit_corrected_yearly.csv'}")
    print(f"Error rates -> {HYPOTHESES_DIR / 'audit_error_rates.csv'}")


if __name__ == "__main__":
    main()
