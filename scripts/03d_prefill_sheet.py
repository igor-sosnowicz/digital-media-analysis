"""Prefill one sheet of an annotation workbook with AI suggestions, which a person then checks (verified = 1).

Works for the source workbooks (pilot, gold, audit, adjudication) and the error
review. The suggestions file has the key columns, `ai_<target>` for each target
column, `ai_uncertain` and `ai_reason`, and no post text, so it is kept in git
(annotations/ai_suggestions/). Readers skip a suggested row until it is verified.
"""

import argparse
from pathlib import Path

import pandas as pd

from digital_media_analysis import ai_suggestions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--sheet", required=True, help="Sheet name, e.g. Reddit, Wikipedia or Błędy.")
    parser.add_argument("--suggestions", type=Path, required=True)
    parser.add_argument("--targets", nargs="+", required=True, help="Columns to prefill, e.g. source_types edit_about_sources.")
    parser.add_argument("--key", nargs="+", default=["unit_id"], help="Columns that identify a row (default: unit_id).")
    parser.add_argument("--source", required=True, help="Who made the suggestions and when, e.g. 'Claude Opus 5.5, 26.10.2026'.")
    args = parser.parse_args()

    suggestions = pd.read_csv(args.suggestions, dtype={column: str for column in args.key})
    if missing := [column for column in [*args.key, *map(ai_suggestions.ai_column, args.targets), "ai_uncertain", "ai_reason"]
                   if column not in suggestions.columns]:
        parser.error(f"{args.suggestions} lacks columns {missing}")
    if suggestions.duplicated(args.key).any():
        parser.error(f"{args.suggestions} has duplicate keys {args.key}")
    filled = ai_suggestions.prefill(args.workbook, args.sheet, args.key, suggestions, args.targets, args.source)
    print(f"{args.workbook} / {args.sheet}: {filled} suggestions")


if __name__ == "__main__":
    main()
