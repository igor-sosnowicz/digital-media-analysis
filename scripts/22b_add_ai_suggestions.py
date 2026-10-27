"""Add AI suggestions to the rows people decide in a plan C review sheet (amendment of 27.10.2026).

Only rows with `decided_by = human` change: the label cell is prefilled with the
suggestion and ai_<target>, ai_uncertain and ai_reason hold it, its doubt and
reason. A row still counts only after a person checks it (`verified = 1`), and
the queue file (annotations/llm/) is not touched, so the rule labels of the
control rows stay there for the precision of the rules. The suggestions file
(annotations/ai_suggestions/) has the key columns, the suggestion column,
ai_uncertain and ai_reason, and no post text. Steps: docs/plan_c_reguly.md.
"""

import argparse
from pathlib import Path

import pandas as pd

from digital_media_analysis import ai_suggestions, llm_annotation


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=llm_annotation.TASKS, required=True)
    parser.add_argument("--sheet-file", type=Path, required=True, help="The review sheet of script 22 (workbook or CSV).")
    parser.add_argument("--sheet")
    parser.add_argument("--key", nargs="+", default=["unit_id"])
    parser.add_argument("--suggestions", type=Path, required=True)
    parser.add_argument("--column", help="Suggestion column in the file (default: ai_<target>).")
    args = parser.parse_args()

    target = llm_annotation.TASKS[args.task].target
    suggestions = pd.read_csv(args.suggestions, dtype={column: str for column in args.key})
    if args.column:
        suggestions = suggestions.rename(columns={args.column: f"ai_{target}"})
    filled = ai_suggestions.fill_queue_rows(args.sheet_file, args.sheet, args.key, suggestions, target)
    print(f"{args.sheet_file}: AI suggestions in {filled} rows for a person")


if __name__ == "__main__":
    main()
