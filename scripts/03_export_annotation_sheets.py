"""Export blind annotation workbooks (one per annotator) for a phase of the gold-standard sample."""

import argparse
import re

from digital_media_analysis import gold
from digital_media_analysis.annotation_sheets import write_workbook
from digital_media_analysis.codebook import load_codebook
from digital_media_analysis.paths import SHEETS_DIR


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=gold.PHASE_SPLITS, default="pilot")
    parser.add_argument("--annotators", nargs="+", default=["A", "B"], help="Short annotator IDs, e.g. initials.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing workbooks.")
    args = parser.parse_args()
    for annotator in args.annotators:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", annotator):
            parser.error(f"Annotator ID {annotator!r} may contain only letters, digits, '-' and '_'.")

    output_paths = {annotator: SHEETS_DIR / f"{args.phase}_{annotator}.xlsx" for annotator in args.annotators}
    existing = [str(path) for path in output_paths.values() if path.exists()]
    if existing and not args.force:
        parser.error(f"Workbooks already exist and may hold annotations: {existing}. Use --force to overwrite.")

    manifest = gold.load_manifest()
    selected = manifest[manifest["split"].isin(gold.PHASE_SPLITS[args.phase])]
    reddit, wikipedia = gold.load_units()
    all_units = {"reddit": reddit, "wikipedia": wikipedia}
    units_by_platform = {
        platform: gold.attach_units(selected[selected["platform"].eq(platform)], units)
        .sort_values(["order", "split"], ignore_index=True)
        for platform, units in all_units.items()
    }

    codebook = load_codebook()
    for annotator, path in output_paths.items():
        write_workbook(path, annotator, args.phase, units_by_platform, codebook)
        print(f"Wrote {path}")
    print(", ".join(f"{platform}: {len(units)}" for platform, units in units_by_platform.items()))


if __name__ == "__main__":
    main()
