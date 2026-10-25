"""Export blind annotation workbooks (one per annotator) for a phase of the gold-standard sample.

By default every unit of the phase goes to every annotator, as agreement needs.
To split a phase between annotators, `--after` names a workbook someone already
coded: the new workbooks then start right after its last coded row, and
`--reddit` / `--wikipedia` cap how many units each platform gets.

`--append` adds to existing workbooks the units of the phase they lack (e.g. a
new pilot round), below their last row; rows already there and their labels
stay as they are. It combines with `--after`, `--reddit` and `--wikipedia`.
"""

import argparse
import re
from pathlib import Path

from digital_media_analysis import gold
from digital_media_analysis.annotation_sheets import append_units, coded_unit_ids, units_after, workbook_metadata, write_workbook
from digital_media_analysis.codebook import load_codebook
from digital_media_analysis.paths import SHEETS_DIR


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=gold.PHASE_SPLITS, default="pilot")
    parser.add_argument("--annotators", nargs="+", default=["A", "B"], help="Short annotator IDs, e.g. initials.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing workbooks.")
    parser.add_argument("--append", action="store_true", help="Add the missing units of the phase to existing workbooks.")
    parser.add_argument("--after", type=Path, help="Workbook of the same phase; export only units after its last coded row.")
    parser.add_argument("--reddit", type=int, help="Reddit units to export (default: all that remain).")
    parser.add_argument("--wikipedia", type=int, help="Wikipedia units to export (default: all that remain).")
    args = parser.parse_args()
    for annotator in args.annotators:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", annotator):
            parser.error(f"Annotator ID {annotator!r} may contain only letters, digits, '-' and '_'.")
    counts = {"reddit": args.reddit, "wikipedia": args.wikipedia}
    if any(count is not None and count < 0 for count in counts.values()):
        parser.error("--reddit and --wikipedia must not be negative.")
    if args.append and args.force:
        parser.error("--append keeps existing workbooks; it cannot be combined with --force.")
    if args.after is not None:
        if not args.after.exists():
            parser.error(f"{args.after} does not exist.")
        if (phase := workbook_metadata(args.after).get("phase")) not in (None, args.phase):
            parser.error(f"{args.after} belongs to phase {phase!r}, not {args.phase!r}.")

    output_paths = {annotator: SHEETS_DIR / f"{args.phase}_{annotator}.xlsx" for annotator in args.annotators}
    existing = [str(path) for path in output_paths.values() if path.exists()]
    if args.append:
        if missing := [str(path) for path in output_paths.values() if not path.exists()]:
            parser.error(f"--append needs existing workbooks; missing: {missing}.")
        for path in output_paths.values():
            if (phase := workbook_metadata(path).get("phase")) not in (None, args.phase):
                parser.error(f"{path} belongs to phase {phase!r}, not {args.phase!r}.")
    elif existing and not args.force:
        parser.error(f"Workbooks already exist and may hold annotations: {existing}. Use --force to overwrite.")

    manifest = gold.load_manifest()
    selected = manifest[gold.phase_mask(manifest, args.phase)]
    reddit, wikipedia = gold.load_units()
    all_units = {"reddit": reddit, "wikipedia": wikipedia}
    units_by_platform = {
        platform: gold.attach_units(selected[selected["platform"].eq(platform)], units)
        .sort_values(gold.PRESENTATION_ORDER[args.phase], ignore_index=True)
        for platform, units in all_units.items()
    }

    coded = coded_unit_ids(args.after) if args.after is not None else {}
    codebook = load_codebook()
    if args.append:
        candidates = {platform: units_after(units, coded.get(platform, [])) for platform, units in units_by_platform.items()}
        for annotator, path in output_paths.items():
            added = append_units(path, candidates, codebook, counts)
            print(f"{path}: added " + ", ".join(f"{platform} {count}" for platform, count in added.items()))
        return

    for platform, units in units_by_platform.items():
        chosen = units_after(units, coded.get(platform, []), counts[platform])
        if len(chosen) < len(units):
            # Rows of the full phase workbook, which every annotator's sheet follows.
            rows = f"rows {chosen.index.min() + 2}-{chosen.index.max() + 2}" if len(chosen) else "no rows"
            print(f"{platform}: {len(chosen)} of {len(units)} units ({rows} of the full {args.phase} workbook)")
        units_by_platform[platform] = chosen.reset_index(drop=True)

    for annotator, path in output_paths.items():
        write_workbook(path, annotator, args.phase, units_by_platform, codebook)
        print(f"Wrote {path}")
    print(", ".join(f"{platform}: {len(units)}" for platform, units in units_by_platform.items()))


if __name__ == "__main__":
    main()
