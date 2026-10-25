"""Import filled stance workbooks into text-free label files and report agreement on shared posts."""

import argparse
import sys

from digital_media_analysis import gold, stance
from digital_media_analysis.codebook import load_codebook
from digital_media_analysis.paths import AGREEMENT_DIR, SHEETS_DIR

MAX_PROBLEMS_SHOWN = 20


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=gold.PHASE_SPLITS, default="pilot")
    parser.add_argument("--check", action="store_true", help="Only validate the workbooks; write nothing.")
    parser.add_argument("--partial", action="store_true", help="Skip rows without labels (a workbook coded in part).")
    args = parser.parse_args()

    paths = stance.workbook_paths(args.phase)
    if not paths:
        sys.exit(f"No workbooks named stance_{args.phase}_<annotator>.xlsx in {SHEETS_DIR}.")
    manifest = gold.load_manifest()
    known = set(manifest.loc[gold.phase_mask(manifest, args.phase) & manifest["platform"].eq("reddit"), "unit_id"].astype(str))
    codebook = load_codebook()

    failed = False
    for annotator, path in paths.items():
        labels, problems = stance.read_workbook(path, codebook, partial=args.partial)
        if outside := sorted(set(labels["unit_id"]) - known):
            problems.append(f"{len(outside)} posts outside phase {args.phase!r}, e.g. {outside[:3]}")
        if mismatched := sorted(set(labels["annotator"].astype(str)) - {annotator}):
            problems.append(f"kolumna annotator zawiera {mismatched}, a plik należy do {annotator!r}")
        if problems:
            failed = True
            print(f"{path.name}: {len(problems)} problem(s)")
            for problem in problems[:MAX_PROBLEMS_SHOWN]:
                print(f"  - {problem}")
        elif args.check:
            print(f"{path.name}: OK, {len(labels)} labels")
        else:
            stance.save_labels(labels, stance.label_path(args.phase, annotator))
            print(f"{path.name}: {len(labels)} labels -> {stance.label_path(args.phase, annotator)}")
    if failed:
        sys.exit("Fix the problems above in the workbooks and run the import again.")

    labels = stance.load_labels(args.phase)
    if not args.check and labels["annotator"].nunique() >= 2:
        table = stance.agreement(labels)
        AGREEMENT_DIR.mkdir(parents=True, exist_ok=True)
        table.to_csv(AGREEMENT_DIR / f"{args.phase}_stance_agreement.csv", index=False, encoding="utf-8")
        for row in table.itertuples(index=False):
            print(f"{row.variable:<17} n={row.units:<4} alpha={row.alpha:.3f} [{row.alpha_low:.3f}, {row.alpha_high:.3f}]")


if __name__ == "__main__":
    main()
