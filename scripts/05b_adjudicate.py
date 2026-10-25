"""Adjudicate disputed units: export the arbiter workbook, then import the arbiter's decisions.

`--export --arbiter ID` writes annotations/sheets/adjudication_<phase>.xlsx with
every unit the annotators of a phase coded differently, and their labels next
to the label columns. `--import` checks the filled workbook and writes the
decisions to annotations/adjudication/<phase>.csv, which instrument validation
uses for those units. The audit phase takes its posts from the H1 audit sample
(annotations/hypotheses/h1_audit_sample.csv); its labels come from
scripts/07c_audit_metrics.py.
"""

import argparse
import re
import sys

import pandas as pd

from digital_media_analysis import adjudication, annotations, gold
from digital_media_analysis.codebook import load_codebook
from digital_media_analysis.paths import HYPOTHESES_DIR

PHASES = [*gold.PHASE_SPLITS, "audit"]


def phase_units(phase: str) -> dict[str, pd.DataFrame]:
    """The units of a phase with their text, per platform, in presentation order."""
    if phase == "audit":
        sample = pd.read_csv(HYPOTHESES_DIR / "h1_audit_sample.csv", dtype={"unit_id": str})
        frame = gold.reddit_units(gold.load_reddit_frame()).set_index("unit_id")
        return {"reddit": frame.loc[sample.sort_values("order")["unit_id"]].reset_index()}
    manifest = gold.load_manifest()
    selected = manifest[gold.phase_mask(manifest, phase)]
    reddit, wikipedia = gold.load_units()
    return {
        platform: gold.attach_units(selected[selected["platform"].eq(platform)], units)
        .sort_values(gold.PRESENTATION_ORDER[phase], ignore_index=True)
        for platform, units in {"reddit": reddit, "wikipedia": wikipedia}.items()
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=PHASES, default="pilot")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--export", action="store_true", help="Write the arbiter workbook.")
    action.add_argument("--import", dest="import_", action="store_true", help="Import the filled arbiter workbook.")
    parser.add_argument("--arbiter", help="Arbiter ID (initials) for --export.")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing arbiter workbook.")
    args = parser.parse_args()

    labels = annotations.load_labels(args.phase)
    if labels["annotator"].nunique() < 2:
        sys.exit(f"Adjudication needs labels from at least two annotators for phase {args.phase!r}.")
    disputes = adjudication.disputed(labels)
    path = adjudication.sheet_path(args.phase)
    codebook = load_codebook()

    if args.export:
        if not args.arbiter or not re.fullmatch(r"[A-Za-z0-9_-]+", args.arbiter):
            parser.error("--export needs --arbiter with letters, digits, '-' or '_' only.")
        if path.exists() and not args.force:
            parser.error(f"{path} exists and may hold decisions; use --force to overwrite.")
        if disputes.empty:
            print(f"No disputed units in phase {args.phase!r}; nothing to adjudicate.")
            return
        counts = adjudication.write_sheet(path, args.phase, args.arbiter, disputes, phase_units(args.phase), codebook)
        print(f"Wrote {path}: " + ", ".join(f"{platform} {count}" for platform, count in counts.items()))
        return

    if not path.exists():
        sys.exit(f"{path} does not exist; export it first with --export.")
    decisions, problems = adjudication.read_decisions(path, codebook, disputes)
    if problems:
        print(f"{path.name}: {len(problems)} problem(s)")
        for problem in problems[:20]:
            print(f"  - {problem}")
        sys.exit("Fix the problems above in the arbiter workbook and import it again.")
    output = adjudication.decisions_path(args.phase)
    adjudication.save_decisions(decisions, output)
    print(f"{path.name}: {len(decisions)} of {len(disputes)} disputed units decided -> {output}")


if __name__ == "__main__":
    main()
