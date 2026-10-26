"""Combine A1 and A2 into suggestions and a human review queue, and write the sheet people work in (plan B).

A row is accepted automatically when both annotators agree, both are confident,
no codebook rule objects and the label is not one that people always check
(e.g. `challenges`); a random 15% of the accepted rows also go to a person as
a control. The queue (annotations/llm/<name>_queue.csv, text-free) keeps each
row's reason and review probability `p_review`. The output sheet is a copy of
the input with the suggestions prefilled: rows with `decided_by = auto` count
as they are, the others wait for `verified = 1`. Steps: docs/plan_b_automatyzacja.md.
"""

import argparse
from pathlib import Path

import pandas as pd

from digital_media_analysis import llm_annotation
from digital_media_analysis.paths import ANNOTATIONS_DIR

OUTPUT_DIR = ANNOTATIONS_DIR / "llm"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=llm_annotation.TASKS, required=True)
    parser.add_argument("--input", type=Path, required=True, help="The same workbook or CSV given to script 19 (the template).")
    parser.add_argument("--sheet")
    parser.add_argument("--key", nargs="+", default=["unit_id"])
    parser.add_argument("--a1", type=Path, required=True, help="Answers of A1 (script 19).")
    parser.add_argument("--a2", type=Path, required=True, help="Answers of A2 (script 19).")
    parser.add_argument("--output", type=Path, required=True, help="The review sheet to write (workbook or CSV).")
    parser.add_argument("--only-empty", action="store_true", help="As in script 19: only rows whose target is still empty.")
    parser.add_argument("--control-share", type=float, default=llm_annotation.CONTROL_SHARE)
    parser.add_argument("--seed", type=int, default=llm_annotation.SEED)
    parser.add_argument("--source", default="A1 Claude, A2 local model, 26.10.2026", help="Shown on the instruction sheet.")
    args = parser.parse_args()

    task = llm_annotation.TASKS[args.task]
    keys = {column: str for column in args.key}
    first = pd.read_csv(args.a1, dtype=keys)
    second = pd.read_csv(args.a2, dtype=keys)
    records = llm_annotation.read_rows(args.input, args.sheet)
    if args.only_empty and task.target in records:
        records = records[records[task.target].fillna("").astype(str).str.strip().eq("")]
    queue = llm_annotation.combine(first, second, records, task, args.key, args.control_share, args.seed)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    queue_path = OUTPUT_DIR / f"{args.output.stem}_queue.csv"
    queue.drop(columns=[column for column in queue.columns if column in task.inputs and column not in args.key]).to_csv(
        queue_path, index=False, encoding="utf-8")
    llm_annotation.write_queue(args.input, args.output, args.sheet, queue, task, args.key, args.source)
    human = queue["decided_by"].eq("human")
    print(f"{len(queue)} rows: {(~human).sum()} accepted automatically, {human.sum()} for a person "
          f"({queue.loc[human, 'queue_reason'].value_counts().to_dict()}); A1 = A2 in {queue['agree'].mean():.0%}")
    print(f"Queue -> {queue_path}; sheet -> {args.output}")


if __name__ == "__main__":
    main()
