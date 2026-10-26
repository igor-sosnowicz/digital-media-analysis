"""Label the rows of an annotation sheet with one LLM annotator (plan B): A1 = Claude API, A2 = a local open model.

Reads the rows of `--input` (a workbook sheet or a CSV), builds the prompt from
the codebook and writes the text-free answers to annotations/llm/<name>_<A1|A2>.csv.
Answers are cached in data/llm_cache/, so a rerun costs nothing. It refuses to
run while the plan B amendment (docs/hipotezy.md) or the annotation code are
uncommitted: the procedure is fixed before any label exists. A1 needs Anthropic
credentials in the environment (ANTHROPIC_API_KEY or `ant auth login`) and the
`llm` group; A2 the `ml` group. Steps: docs/plan_b_automatyzacja.md.
"""

import argparse
import sys
from pathlib import Path

from digital_media_analysis import llm_annotation, prereg
from digital_media_analysis.codebook import load_codebook
from digital_media_analysis.paths import ANNOTATIONS_DIR

FROZEN = ["docs/hipotezy.md", "codebook/codebook.yaml", "src/digital_media_analysis/llm_annotation.py",
          "scripts/19_llm_annotate.py", "scripts/20_review_queue.py"]
OUTPUT_DIR = ANNOTATIONS_DIR / "llm"


def output_path(input_path: Path, sheet: str | None, annotator: str) -> Path:
    stem = input_path.stem + (f"_{sheet}" if sheet and input_path.suffix.lower() != ".csv" else "")
    return OUTPUT_DIR / f"{stem}_{annotator}.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=llm_annotation.TASKS, required=True)
    parser.add_argument("--input", type=Path, required=True, help="Workbook (with --sheet) or CSV whose rows are labelled.")
    parser.add_argument("--sheet", help="Sheet name of a workbook, e.g. Reddit, Wikipedia or Błędy.")
    parser.add_argument("--key", nargs="+", default=["unit_id"], help="Columns that identify a row.")
    parser.add_argument("--annotator", choices=["A1", "A2"], required=True)
    parser.add_argument("--model", help="Override the model (default: claude-opus-5-5 for A1, Qwen/Qwen2.5-3B-Instruct for A2).")
    parser.add_argument("--only-empty", action="store_true", help="Label only rows whose target column is still empty.")
    parser.add_argument("--allow-uncommitted", action="store_true", help="For a dry run on test data only.")
    args = parser.parse_args()

    if (dirty := prereg.uncommitted(FROZEN)) and not args.allow_uncommitted:
        sys.exit(f"Commit the plan B amendment and the annotation code first (docs/hipotezy.md):\n{dirty}")
    task = llm_annotation.TASKS[args.task]
    rows = llm_annotation.read_rows(args.input, args.sheet)
    if args.only_empty and task.target in rows:
        rows = rows[rows[task.target].fillna("").astype(str).str.strip().eq("")]
    if rows.empty:
        sys.exit("No rows to label.")
    if args.annotator == "A1":
        annotator = llm_annotation.claude_annotator(**({"model": args.model} if args.model else {}))
    else:
        annotator = llm_annotation.local_annotator(**({"model": args.model} if args.model else {}))

    def progress(done: int, total: int) -> None:
        if done % 25 == 0 or done == total:
            print(f"  {done}/{total}", flush=True)

    codebook = load_codebook()
    answers = annotator.annotate(task, rows.to_dict("records"), args.key, codebook, progress)
    path = output_path(args.input, args.sheet, args.annotator)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    answers.to_csv(path, index=False, encoding="utf-8")
    print(f"{annotator.model}: {len(answers)} rows, {answers['label'].isna().sum()} without a usable answer -> {path}")
    print(answers["label"].value_counts(dropna=False).head(10).to_string())


if __name__ == "__main__":
    main()
