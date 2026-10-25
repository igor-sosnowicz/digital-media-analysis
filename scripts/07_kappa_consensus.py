"""Cohen's kappa between annotator pairs and a consensus file of single-label agreements.

Reads imported labels for a phase, computes Cohen's kappa per annotator pair
and variable, and writes two tables into `annotations/agreement/`:
- `<phase>_kappa.csv` — kappa with a bootstrap interval per pair and variable
- `<phase>_consensus.csv` — units where both annotators of a pair assigned the
  same single label (identical 0/1, or exactly one identical source type;
  `none` counts as a single label, multi-code agreement does not)

Run:

    uv run scripts/07_kappa_consensus.py --phase gold --annotators JP IS
"""

import argparse
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from digital_media_analysis import agreement, annotations, gold
from digital_media_analysis.codebook import load_codebook
from digital_media_analysis.paths import AGREEMENT_DIR

KAPPA_COLUMNS = [
    "platform", "pair", "annotator_1", "annotator_2", "variable", "units",
    "phase_units", "coverage", "observed_agreement", "kappa", "kappa_low", "kappa_high",
]
CONSENSUS_COLUMNS = [
    "unit_id", "platform", "pair", "annotator_1", "annotator_2", "variable",
    "label", "value_1", "value_2", "uncertain",
]


def kappa_table(
    labels: pd.DataFrame,
    category_codes: list[str],
    samples: int,
    seed: int,
    manifest: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Cohen's kappa per annotator pair, platform and variable.

    Only units where both annotators of a pair actually provided a usable
    label are included — units missing from either annotator are dropped,
    so kappas are never computed over units one of them never coded.
    """
    # Phase units per platform, for coverage reporting (phase units actually
    # present in the manifest, not just the units that happen to be labeled).
    phase_units_by_platform: dict[str, set[str]] = {}
    if manifest is not None:
        for platform, platform_manifest in manifest.groupby("platform"):
            phase_units_by_platform[platform] = set(platform_manifest["unit_id"])

    rows = []
    for platform, platform_labels in labels.groupby("platform"):
        annotators = sorted(platform_labels["annotator"].unique())
        variables = agreement.variables_for(platform, category_codes)
        phase_units = phase_units_by_platform.get(platform, set())
        for first, second in itertools.combinations(annotators, 2):
            pair = platform_labels[platform_labels["annotator"].isin({first, second})]
            units_first = set(pair[pair["annotator"].eq(first)]["unit_id"])
            units_second = set(pair[pair["annotator"].eq(second)]["unit_id"])
            shared_units = units_first & units_second
            if not shared_units:
                continue
            pair = pair[pair["unit_id"].isin(shared_units)]
            for variable in variables:
                matrix = agreement.value_matrix(pair, variable)
                paired = matrix.dropna(subset=[first, second])
                if paired.empty:
                    continue
                estimate = agreement.cohen_kappa(
                    paired[first].tolist(), paired[second].tolist(), samples, seed
                )
                phase_total = len(phase_units)
                coverage = len(paired) / phase_total if phase_total else None
                rows.append({
                    "platform": platform,
                    "pair": f"{first}–{second}",
                    "annotator_1": first,
                    "annotator_2": second,
                    "variable": variable,
                    "units": len(paired),
                    "phase_units": phase_total,
                    "coverage": coverage,
                    "observed_agreement": float(np.mean(paired[first] == paired[second])),
                    "kappa": estimate.value,
                    "kappa_low": estimate.low,
                    "kappa_high": estimate.high,
                })
    if not rows:
        return pd.DataFrame(columns=KAPPA_COLUMNS)
    return pd.DataFrame(rows, columns=KAPPA_COLUMNS)


def consensus_cases(labels: pd.DataFrame) -> pd.DataFrame:
    """Units where both annotators of a pair agree on a single label.

    Only the primary label variables are compared: `cites_source` (both 0 or
    both 1) and `source_types` (exactly one identical code; `none` included).
    Derived indicators (`source_types:<code>`) and platform-specific binaries
    are left out, since agreeing on their absence is not a single label.
    """
    rows = []
    for platform, platform_labels in labels.groupby("platform"):
        annotators = sorted(platform_labels["annotator"].unique())
        for first, second in itertools.combinations(annotators, 2):
            pair = platform_labels[platform_labels["annotator"].isin({first, second})]
            uncertain = pair.pivot(index="unit_id", columns="annotator", values="uncertain")
            for variable in ("cites_source", "source_types"):
                matrix = agreement.value_matrix(pair, variable)
                paired = matrix.dropna(subset=[first, second])
                for unit_id, row in paired.iterrows():
                    first_value, second_value = row[first], row[second]
                    if first_value != second_value:
                        continue
                    label = _single_label(first_value)
                    if label is None:
                        continue
                    rows.append({
                        "unit_id": unit_id,
                        "platform": platform,
                        "pair": f"{first}–{second}",
                        "annotator_1": first,
                        "annotator_2": second,
                        "variable": variable,
                        "label": label,
                        "value_1": _display(first_value),
                        "value_2": _display(second_value),
                        "uncertain": ", ".join(
                            annotator
                            for annotator, flag in uncertain.loc[unit_id].items()
                            if not pd.isna(flag) and flag == 1
                        ),
                    })
    if not rows:
        return pd.DataFrame(columns=CONSENSUS_COLUMNS)
    return pd.DataFrame(rows, columns=CONSENSUS_COLUMNS)


def _single_label(value: object) -> str | None:
    """The single code of a label, or None when it is not a single label."""
    if isinstance(value, frozenset):
        if len(value) == 1:
            return next(iter(value))
        if not value:
            return "none"
        return None  # multi-code agreement is not a single label
    if pd.isna(value):
        return None
    return str(int(value))


def _display(value: object) -> str:
    if isinstance(value, frozenset):
        return ";".join(sorted(value)) or "none"
    if pd.isna(value):
        return ""
    return str(int(value))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=gold.PHASE_SPLITS, default="pilot")
    parser.add_argument("--annotators", nargs="*", help="Only these annotators (default: all).")
    parser.add_argument("--kappa-out", type=Path, help="Output table of kappas (default: annotations/agreement/<phase>_kappa.csv).")
    parser.add_argument("--consensus-out", type=Path, help="Output table of consensus cases (default: annotations/agreement/<phase>_consensus.csv).")
    parser.add_argument("--samples", type=int, default=agreement.BOOTSTRAP_SAMPLES, help="Bootstrap replicates for kappa intervals.")
    parser.add_argument("--seed", type=int, default=agreement.SEED, help="Bootstrap seed.")
    args = parser.parse_args(argv)

    labels = annotations.load_labels(args.phase, labels_dir=annotations.LABELS_DIR)
    if labels["annotator"].nunique() < 2:
        sys.exit(
            f"Kappa needs labels from at least two annotators; import them with "
            f"scripts/04_import_annotations.py --phase {args.phase}."
        )
    if args.annotators:
        labels = labels[labels["annotator"].isin(args.annotators)]
        if labels["annotator"].nunique() < 2:
            sys.exit(
                f"Fewer than two annotators left after the --annotators filter: "
                f"{sorted(labels['annotator'].unique())}."
            )

    codebook = load_codebook()
    try:
        manifest = gold.load_manifest()
        manifest = manifest[manifest["split"].isin(gold.PHASE_SPLITS[args.phase])]
    except FileNotFoundError:
        manifest = None
    table = kappa_table(labels, codebook.category_codes, args.samples, args.seed, manifest)
    consensus = consensus_cases(labels)

    AGREEMENT_DIR.mkdir(parents=True, exist_ok=True)
    kappa_out = args.kappa_out or AGREEMENT_DIR / f"{args.phase}_kappa.csv"
    consensus_out = args.consensus_out or AGREEMENT_DIR / f"{args.phase}_consensus.csv"
    table.to_csv(kappa_out, index=False, encoding="utf-8")
    consensus.to_csv(consensus_out, index=False, encoding="utf-8")

    for row in table.itertuples(index=False):
        cov = f"cov={row.coverage:.0%}" if row.coverage is not None else "cov=n/a"
        print(
            f"{row.platform:<10} {row.pair:<16} {row.variable:<26} n={row.units:<4} "
            f"({cov}) kappa={row.kappa:.3f} [{row.kappa_low:.3f}, {row.kappa_high:.3f}]  "
            f"agree={row.observed_agreement:.3f}"
        )
    print(f"Consensus cases: {len(consensus)}. Wrote {kappa_out} and {consensus_out}")


if __name__ == "__main__":
    main()
