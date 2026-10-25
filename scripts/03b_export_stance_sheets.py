"""Export stance workbooks (`consensus_stance`, Reddit only) for a phase of the gold-standard sample.

By default every Reddit unit of the phase goes to every annotator. `--splits`
keeps only some splits (e.g. the second pilot round, `pilot2`), and `--units-from`
keeps the units someone labelled in a source workbook, so each annotator codes
the stance of the posts they already coded for sources.
"""

import argparse
import re
from pathlib import Path

from digital_media_analysis import gold, stance
from digital_media_analysis.annotation_sheets import coded_unit_ids
from digital_media_analysis.codebook import load_codebook


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=gold.PHASE_SPLITS, default="pilot")
    parser.add_argument("--annotators", nargs="+", required=True, help="Short annotator IDs, e.g. initials.")
    parser.add_argument("--splits", nargs="+", help="Keep only these splits of the phase, e.g. pilot2.")
    parser.add_argument("--units-from", type=Path, help="Keep only the Reddit units labelled in this workbook.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing stance workbooks.")
    args = parser.parse_args()
    for annotator in args.annotators:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", annotator):
            parser.error(f"Annotator ID {annotator!r} may contain only letters, digits, '-' and '_'.")
    paths = {annotator: stance.workbook_path(args.phase, annotator) for annotator in args.annotators}
    if (existing := [str(path) for path in paths.values() if path.exists()]) and not args.force:
        parser.error(f"Stance workbooks already exist and may hold labels: {existing}. Use --force to overwrite.")

    manifest = gold.load_manifest()
    selected = manifest[gold.phase_mask(manifest, args.phase) & manifest["platform"].eq("reddit")]
    if args.splits:
        selected = selected[selected["split"].isin(args.splits)]
    reddit, _ = gold.load_units()
    units = gold.attach_units(selected, reddit).sort_values(gold.PRESENTATION_ORDER[args.phase], ignore_index=True)
    if args.units_from is not None:
        keep = set(coded_unit_ids(args.units_from).get("reddit", []))
        units = units[units["unit_id"].astype(str).isin(keep)].reset_index(drop=True)
    if units.empty:
        parser.error("No Reddit units selected.")

    codebook = load_codebook()
    for annotator, path in paths.items():
        stance.write_workbook(path, annotator, args.phase, units, codebook)
        print(f"Wrote {path} ({len(units)} posts; splits {units['split'].value_counts().to_dict()})")


if __name__ == "__main__":
    main()
