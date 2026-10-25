"""Import filled annotation workbooks into text-free label files in `annotations/labels/`.

Rows with invalid labels (unknown codes, empty `source_types`, `none` with other
codes, a value other than 0/1) are left out of the label file and listed, so one
bad row does not stop the import. Problems of the whole workbook (wrong headers,
units outside the phase, repeated units, missing units without `--partial`,
another person in the `annotator` column) stop it: nothing is written for that
workbook and the script exits with an error.
"""

import argparse
import sys

from digital_media_analysis import annotations, gold
from digital_media_analysis.codebook import load_codebook
from digital_media_analysis.paths import SHEETS_DIR

MAX_PROBLEMS_SHOWN = 20


def show(problems: list[str]) -> None:
    for problem in problems[:MAX_PROBLEMS_SHOWN]:
        print(f"  - {problem}")
    if len(problems) > MAX_PROBLEMS_SHOWN:
        print(f"  ... and {len(problems) - MAX_PROBLEMS_SHOWN} more")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=gold.PHASE_SPLITS, default="pilot")
    parser.add_argument("--check", action="store_true", help="Only validate the workbooks; write nothing.")
    parser.add_argument(
        "--partial",
        action="store_true",
        help="The phase is split between annotators: skip rows without labels and allow missing units.",
    )
    args = parser.parse_args()

    paths = annotations.workbook_paths(args.phase)
    if not paths:
        sys.exit(f"No workbooks named {args.phase}_<annotator>.xlsx in {SHEETS_DIR}.")
    manifest = gold.load_manifest()
    codebook = load_codebook()

    failed = False
    for annotator, path in paths.items():
        labels, problems = annotations.import_workbook(path, annotator, args.phase, manifest, codebook, partial=args.partial)
        labels, dropped, blocking = annotations.drop_invalid_rows(labels, problems)
        if dropped:
            print(f"{path.name}: {len(dropped)} row(s) with invalid labels left out")
            show(dropped)
        if blocking:
            failed = True
            print(f"{path.name}: {len(blocking)} problem(s) of the whole workbook; nothing written")
            show(blocking)
            continue
        if args.check:
            print(f"{path.name}: validated, {len(labels)} label(s)")
        else:
            output_path = annotations.label_path(args.phase, annotator)
            annotations.save_labels(labels, output_path)
            print(f"{path.name}: {len(labels)} label(s) -> {output_path}")
    if failed:
        sys.exit("Fix the workbook problems above and run the import again.")


if __name__ == "__main__":
    main()
