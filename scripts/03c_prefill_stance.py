"""Prefill stance workbooks with AI suggestions, which each person then checks (verified = 1).

The suggestions file (unit_id, ai_stance, ai_uncertain, ai_reason) has no post
text and is kept in git, so the AI's part in the labels can be shown. The
suggestion stays in the workbook next to the person's label; the import counts
a row only once it is verified and reports how many suggestions were changed.
"""

import argparse
from pathlib import Path

import pandas as pd

from digital_media_analysis import gold, stance
from digital_media_analysis.codebook import load_codebook
from digital_media_analysis.paths import PROJECT_ROOT


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=gold.PHASE_SPLITS, required=True)
    parser.add_argument("--suggestions", type=Path, required=True, help="CSV with unit_id, ai_stance, ai_uncertain, ai_reason.")
    parser.add_argument("--source", required=True, help="Who made the suggestions and when, e.g. 'Claude Opus 5.5, 26.10.2026'.")
    parser.add_argument("--annotators", nargs="+", help="Only these annotators' workbooks (default: all of the phase).")
    args = parser.parse_args()

    suggestions = pd.read_csv(args.suggestions, dtype={"unit_id": str, "ai_stance": str, "ai_reason": str})
    allowed = set(stance.stance_values(load_codebook()))
    if bad := sorted(set(suggestions["ai_stance"]) - allowed):
        parser.error(f"Suggestions outside {sorted(allowed)}: {bad}")
    if suggestions["unit_id"].duplicated().any():
        parser.error("The suggestions file has a unit_id more than once.")
    paths = stance.workbook_paths(args.phase)
    if args.annotators:
        paths = {annotator: path for annotator, path in paths.items() if annotator in args.annotators}
    if not paths:
        parser.error(f"No stance workbooks of phase {args.phase!r} to prefill.")
    for annotator, path in paths.items():
        filled = stance.add_ai_suggestions(path, suggestions, args.source)
        print(f"{path.relative_to(PROJECT_ROOT)}: {filled} suggestions")


if __name__ == "__main__":
    main()
