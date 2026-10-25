"""Combine both annotators' labels into a single dataset per phase.

Reads imported labels for a phase and writes one combined CSV where every
annotator's label is a row. Units where both annotators labeled get both rows
(with an `agrees` flag showing whether they match on `source_types`).

Units with blank `source_types` (missing labels) are excluded.

Run:

    uv run scripts/08_combine_labels.py --phase gold
    uv run scripts/08_combine_labels.py --phase pilot
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

from digital_media_analysis import annotations, gold
from digital_media_analysis.paths import AGREEMENT_DIR


def combine_labels(labels: pd.DataFrame) -> pd.DataFrame:
    """Return combined labels, one row per annotator per unit, blanks excluded."""
    if labels.empty:
        return pd.DataFrame(
            columns=[
                "unit_id", "platform", "annotator", "source_types",
                "cites_source", "uncertain", "notes", "n_annotators", "agrees",
            ]
        )

    # Only units that have at least one filled source_types label.
    labeled = labels[labels["source_types"].notna() & (labels["source_types"] != "")].copy()

    if labeled.empty:
        return pd.DataFrame(
            columns=[
                "unit_id", "platform", "annotator", "source_types",
                "cites_source", "uncertain", "notes", "n_annotators", "agrees",
            ]
        )

    # Count how many annotators labeled each unit.
    counts = labeled.groupby(["unit_id", "platform"]).size().rename("n_annotators")
    labeled = labeled.merge(counts, on=["unit_id", "platform"], how="left")

    # Agreement flag: for units with 2 annotators, do their source_types match?
    two = labeled[labeled["n_annotators"].eq(2)]
    labeled["agrees"] = pd.NA
    if not two.empty:
        pivot = two.pivot_table(
            index=["unit_id", "platform"], columns="annotator", values="source_types",
            aggfunc="first",
        )
        match = pivot.iloc[:, 0].eq(pivot.iloc[:, 1])
        agree_map = match.reset_index().rename(columns={0: "agrees"})
        # Drop pre-existing agrees column to avoid _x/_y suffixes on merge.
        labeled = labeled.drop(columns=["agrees"]).merge(
            agree_map, on=["unit_id", "platform"], how="left"
        )

    column_order = [
        "unit_id", "platform", "annotator", "source_types",
        "cites_source", "uncertain", "notes", "n_annotators", "agrees",
    ]
    return labeled.sort_values(["platform", "unit_id", "annotator"], ignore_index=True)[
        column_order
    ]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=gold.PHASE_SPLITS, default="pilot")
    parser.add_argument("--out", type=Path, help="Output CSV (default: annotations/agreement/<phase>_combined.csv).")
    args = parser.parse_args(argv)

    labels = annotations.load_labels(args.phase)
    if labels["annotator"].nunique() < 2:
        sys.exit(
            f"Combine needs labels from at least two annotators; import them with "
            f"scripts/04_import_annotations.py --phase {args.phase}."
        )

    combined = combine_labels(labels)

    AGREEMENT_DIR.mkdir(parents=True, exist_ok=True)
    out = args.out or AGREEMENT_DIR / f"{args.phase}_combined.csv"
    combined.to_csv(out, index=False, encoding="utf-8")

    n_units = combined["unit_id"].nunique()
    n_two = (combined["n_annotators"] == 2).sum() // 2
    n_agree = int(combined["agrees"].eq(True).sum() // 2)
    print(f"Units with at least one label: {n_units}")
    print(f"Units annotated by both: {n_two} (agree on source_types: {n_agree})")
    print(f"Total annotator-rows: {len(combined)}")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
