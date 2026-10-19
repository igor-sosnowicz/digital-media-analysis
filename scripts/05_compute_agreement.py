"""Compute inter-annotator agreement for a phase and save tables and a plot to `annotations/agreement/`."""

import argparse
import sys

import matplotlib

matplotlib.use("Agg")

from digital_media_analysis import agreement, annotations, gold  # noqa: E402
from digital_media_analysis.codebook import load_codebook  # noqa: E402
from digital_media_analysis.paths import AGREEMENT_DIR  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=gold.PHASE_SPLITS, default="pilot")
    parser.add_argument("--samples", type=int, default=agreement.BOOTSTRAP_SAMPLES, help="Bootstrap replicates.")
    args = parser.parse_args()

    labels = annotations.load_labels(args.phase)
    if labels["annotator"].nunique() < 2:
        sys.exit(f"Agreement needs labels from at least two annotators; import them with scripts/04_import_annotations.py --phase {args.phase}.")
    codebook = load_codebook()

    table = agreement.agreement_table(labels, codebook.category_codes, samples=args.samples)
    outputs = {
        "agreement": table,
        "disagreements": agreement.disagreements(labels),
        "annotators": agreement.annotator_summary(labels).reset_index(),
    }
    AGREEMENT_DIR.mkdir(parents=True, exist_ok=True)
    for name, frame in outputs.items():
        frame.to_csv(AGREEMENT_DIR / f"{args.phase}_{name}.csv", index=False, encoding="utf-8")
    agreement.plot_alpha(table, AGREEMENT_DIR / f"{args.phase}_alpha.png")

    headline = table[~table["variable"].str.startswith("source_types:")]
    for row in headline.itertuples(index=False):
        print(
            f"{row.platform:<10} {row.variable:<20} n={row.units:<4} "
            f"alpha={row.alpha:.3f} [{row.alpha_low:.3f}, {row.alpha_high:.3f}]  {row.verdict}"
        )
    print(f"Disagreements: {len(outputs['disagreements'])}. Tables and plot written to {AGREEMENT_DIR}")


if __name__ == "__main__":
    main()
