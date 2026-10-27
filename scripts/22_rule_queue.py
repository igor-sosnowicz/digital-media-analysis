"""Plan C: label what codebook rules decide alone and write the sheet in which people code the rest.

No language model takes part (rule_annotation.py). Rows a rule decides are
prefilled and count as they are (`decided_by = auto`); a random 15% of them and
every row no rule decides go to a person, who codes them blind (no label shown)
and sets `verified = 1`. The queue with the rule labels, reasons and `p_review`
goes to annotations/llm/<name>_queue.csv (text-free); scripts/21 then estimates
each rule's precision on the control rows. It refuses to run while the plan C
amendment (docs/hipotezy.md) or the rule code are uncommitted. Steps: docs/plan_c_reguly.md.
"""

import argparse
import sys
from pathlib import Path

from digital_media_analysis import llm_annotation, prereg, rule_annotation
from digital_media_analysis.paths import ANNOTATIONS_DIR

FROZEN = ["docs/hipotezy.md", "codebook/codebook.yaml", "codebook/topics.yaml",
          "src/digital_media_analysis/rule_annotation.py", "scripts/22_rule_queue.py"]
OUTPUT_DIR = ANNOTATIONS_DIR / "llm"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=llm_annotation.TASKS, required=True)
    parser.add_argument("--input", type=Path, required=True, help="Blank template workbook (with --sheet) or CSV.")
    parser.add_argument("--sheet")
    parser.add_argument("--key", nargs="+", default=["unit_id"])
    parser.add_argument("--output", type=Path, required=True, help="The sheet people work in (workbook or CSV).")
    parser.add_argument("--only-empty", action="store_true", help="Only rows whose target column is still empty.")
    parser.add_argument("--control-share", type=float, default=rule_annotation.CONTROL_SHARE)
    parser.add_argument("--seed", type=int, default=rule_annotation.SEED)
    parser.add_argument("--allow-uncommitted", action="store_true", help="For a dry run on test data only.")
    args = parser.parse_args()

    if (dirty := prereg.uncommitted(FROZEN)) and not args.allow_uncommitted:
        sys.exit(f"Commit the plan C amendment and the rule code first (docs/hipotezy.md):\n{dirty}")
    task = llm_annotation.TASKS[args.task]
    records = llm_annotation.read_rows(args.input, args.sheet)
    if args.only_empty and task.target in records:
        records = records[records[task.target].fillna("").astype(str).str.strip().eq("")]
    if records.empty:
        sys.exit("No rows.")
    rule_queue = rule_annotation.queue(records, args.task, args.key, args.control_share, args.seed)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    queue_path = OUTPUT_DIR / f"{args.output.stem}_queue.csv"
    rule_queue.to_csv(queue_path, index=False, encoding="utf-8")
    llm_annotation.write_queue(args.input, args.output, args.sheet, rule_annotation.sheet_view(rule_queue), task, args.key,
                               "reguły codebooka (plan C), bez modeli językowych")
    human = rule_queue["decided_by"].eq("human")
    print(f"{len(rule_queue)} rows: {(~human).sum()} decided by a rule, {human.sum()} for a person "
          f"({rule_queue.loc[human, 'queue_reason'].value_counts().to_dict()})")
    print(rule_queue.loc[rule_queue["rule"].ne(""), "rule"].value_counts().to_string())
    print(f"Queue -> {queue_path}; sheet -> {args.output}")


if __name__ == "__main__":
    main()
