"""Import filled annotation workbooks into text-free label files in `annotations/labels/`."""

import argparse
import sys

from digital_media_analysis import annotations, gold
from digital_media_analysis.codebook import load_codebook
from digital_media_analysis.paths import SHEETS_DIR

MAX_PROBLEMS_SHOWN = 20


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=gold.PHASE_SPLITS, default="pilot")
    parser.add_argument("--check", action="store_true", help="Only validate the workbooks; write nothing.")
    args = parser.parse_args()

    paths = annotations.workbook_paths(args.phase)
    if not paths:
        sys.exit(f"No workbooks named {args.phase}_<annotator>.xlsx in {SHEETS_DIR}.")
    manifest = gold.load_manifest()
    codebook = load_codebook()

    for annotator, path in paths.items():
        labels, problems = annotations.import_workbook(path, annotator, args.phase, manifest, codebook)
        if problems:
            print(f"{path.name}: {len(problems)} problem(s), writing {len(labels)} valid label(s)")
            for problem in problems[:MAX_PROBLEMS_SHOWN]:
                print(f"  - {problem}")
            if len(problems) > MAX_PROBLEMS_SHOWN:
                print(f"  ... and {len(problems) - MAX_PROBLEMS_SHOWN} more")
        if args.check:
            print(f"{path.name}: validated, {len(labels)} label(s)")
        else:
            output_path = annotations.label_path(args.phase, annotator)
            annotations.save_labels(labels, output_path)
            print(f"{path.name}: {len(labels)} label(s) -> {output_path}")


if __name__ == "__main__":
    main()
