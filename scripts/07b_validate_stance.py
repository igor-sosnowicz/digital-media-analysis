"""Validate the stance instrument (stance_v1) on human `consensus_stance` labels of the gold sample.

`--split dev --tune` searches the three thresholds on the dev split (weighted
macro-F1 over the stance values); with `--apply` it also writes the best ones
into `instruments/stance_v1.py` and sets `TUNED = True`, to be committed.
`--split test --frozen` then runs the test split once; it refuses while the
stance code is uncommitted or not tuned, or when the test split already ran.
The test run checks the validity gate of the preregistration (docs/hipotezy.md:
F1 of `challenges` >= 0.5 and kappa >= 0.4) and records it in
stance_test_run.json; scripts/08 labels the H1 sample only when it passed.
Results go to annotations/validation/stance_<split>_*.csv. Needs the `ml` dependency group.

Plan B (docs/hipotezy.md, 26.10.2026): the reference also takes the enriched
r/conspiracy sample (phase `enriched`, weights 1 / inclusion) and labels the
LLM review queue accepted automatically. Tuning uses all reference rows; the
gate is decided on the rows a person decided, weighted by 1 / p_review, and
reported on all rows as a sensitivity analysis.
"""

import argparse
import itertools
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from digital_media_analysis import gold, hypotheses, stance, validation
from digital_media_analysis.codebook import load_codebook
from digital_media_analysis.instruments import stance_v1
from digital_media_analysis.paths import HYPOTHESES_DIR, MODEL_CACHE_DIR, PREDICTIONS_DIR, PROJECT_ROOT, VALIDATION_DIR

FROZEN_PATHS = ["src/digital_media_analysis/instruments/stance_v1.py", "src/digital_media_analysis/instruments/nli.py",
                "src/digital_media_analysis/validation.py", "src/digital_media_analysis/stance.py", "scripts/07b_validate_stance.py"]
ENRICHED_SAMPLE = HYPOTHESES_DIR / "stance_enriched_sample.csv"
GRID = [round(value, 2) for value in np.arange(0.3, 0.91, 0.1)]
# Validity gate of H1-A (docs/hipotezy.md), checked on the test split.
GATE = {"challenges_f1": 0.5, "kappa": 0.4}
INSTRUMENT_PATH = PROJECT_ROOT / "src" / "digital_media_analysis" / "instruments" / "stance_v1.py"


def apply_thresholds(thresholds: dict[str, float], path: Path = INSTRUMENT_PATH) -> None:
    """Write the chosen thresholds into the instrument and mark it tuned (the change is then committed by a person)."""
    text = path.read_text(encoding="utf-8")
    values = ", ".join(f'"{name}": {thresholds[name]}' for name in ["relevance", "supports", "challenges"])
    text, replaced = re.subn(r"^THRESHOLDS = \{.*\}$", f"THRESHOLDS = {{{values}}}", text, flags=re.MULTILINE)
    text, tuned = re.subn(r"^TUNED = (True|False)$", "TUNED = True", text, flags=re.MULTILINE)
    if replaced != 1 or tuned != 1:
        raise RuntimeError(f"Could not find THRESHOLDS and TUNED in {path}")
    path.write_text(text, encoding="utf-8")


def gate(metrics: dict[str, float]) -> dict:
    challenges_f1, kappa = metrics.get("challenges:f1", float("nan")), metrics.get("kappa", float("nan"))
    passed = bool(challenges_f1 >= GATE["challenges_f1"] and kappa >= GATE["kappa"])
    return {"challenges_f1": challenges_f1, "kappa": kappa, "thresholds": GATE, "passed": passed}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True, check=True).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=["dev", "test"], default="dev")
    parser.add_argument("--tune", action="store_true", help="Dev only: search the thresholds.")
    parser.add_argument("--frozen", action="store_true", help="Required for the test split.")
    parser.add_argument("--apply", action="store_true", help="With --tune: write the best thresholds into stance_v1.py.")
    parser.add_argument("--refresh", action="store_true", help="Recompute model output instead of reading the cache.")
    args = parser.parse_args()
    head, dirty = git("rev-parse", "HEAD"), git("status", "--porcelain", "--", *FROZEN_PATHS)
    if args.split == "test":
        if args.tune or not args.frozen:
            parser.error("The test split runs once on the frozen, tuned instrument: no --tune, and pass --frozen.")
        if not stance_v1.TUNED:
            sys.exit("stance_v1 is not tuned: tune it on dev, set TUNED = True and commit first.")
        if dirty:
            sys.exit(f"Commit the stance instrument and validation code before the test run:\n{dirty}")
        if (VALIDATION_DIR / "stance_test_run.json").exists():
            sys.exit("The stance test split already ran (annotations/validation/stance_test_run.json); it runs once.")
    elif args.tune is False and not stance_v1.TUNED:
        print("Note: stance_v1 is not tuned; these are the placeholder thresholds.")

    classes = stance.stance_values(load_codebook())
    manifest = gold.load_manifest()
    gold_labels = stance.load_labels("gold")
    enriched_labels = stance.load_labels(stance.ENRICHED_PHASE)
    enriched_sample = pd.read_csv(ENRICHED_SAMPLE, dtype={"unit_id": str}) if ENRICHED_SAMPLE.exists() else None
    if gold_labels.empty and enriched_labels.empty:
        sys.exit("No stance labels yet: export stance sheets (03b, 03e), code or review them, import them (04b).")
    for labels in [gold_labels, enriched_labels]:
        if len(conflicts := stance.reference(labels)[1]):
            print(f"{conflicts['unit_id'].nunique()} posts with different stances are left out until adjudicated.")
    frame = stance.validation_frame(gold_labels, manifest, args.split, enriched_labels, enriched_sample).set_index("unit_id")
    print(f"{args.split}: {frame['source'].value_counts().to_dict()} posts; decided by a person: "
          f"{frame['decided_by'].eq('human').sum()}")
    reddit, _ = gold.load_units()
    gold_ids = frame.index[frame["source"].eq("gold")]
    units = reddit[reddit["unit_id"].isin(gold_ids)].reset_index(drop=True)
    scores = hypotheses.cached_scores(MODEL_CACHE_DIR / f"stance_v1_{args.split}.csv", units, stance_v1.score, refresh=args.refresh)
    if (enriched_ids := frame.index[frame["source"].eq(stance.ENRICHED_PHASE)]).size:
        # Enriched posts come from the H1 sample, whose model output is cached already.
        cached = pd.read_csv(MODEL_CACHE_DIR / "stance_v1_h1.csv", dtype={"unit_id": str}, keep_default_na=False)
        scores = pd.concat([scores, cached[cached["unit_id"].isin(enriched_ids)]], ignore_index=True)
        if missing := sorted(set(enriched_ids) - set(scores["unit_id"])):
            sys.exit(f"{len(missing)} enriched posts lack cached stance_v1 output, e.g. {missing[:3]}")
    truth = frame[stance.STANCE]
    reviewed = frame[frame["review_weight"].notna()]

    def evaluate(thresholds: dict[str, float] | None, rows: pd.DataFrame = frame, weight: str = "weight") -> dict[str, float]:
        predicted = stance_v1.labels(scores, thresholds).set_index("unit_id")[stance.STANCE]
        return validation.nominal_metrics(rows[stance.STANCE], predicted.loc[rows.index], rows[weight], classes)

    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    if args.tune:
        rows = []
        for relevance, supports, challenges in itertools.product(GRID, GRID, GRID):
            thresholds = {"relevance": relevance, "supports": supports, "challenges": challenges}
            rows.append({**thresholds, **evaluate(thresholds)})
        grid = pd.DataFrame(rows).sort_values(["macro_f1", "accuracy"], ascending=False)
        grid.to_csv(VALIDATION_DIR / "stance_dev_tuning.csv", index=False, encoding="utf-8")
        shown = ["relevance", "supports", "challenges", "macro_f1", "challenges:f1", "kappa", "accuracy"]
        print(f"Best thresholds on dev (weighted macro-F1):\n{grid[shown].head(5).round(3).to_string(index=False)}")
        if args.apply:
            best = grid.iloc[0]
            apply_thresholds({name: float(best[name]) for name in ["relevance", "supports", "challenges"]})
            stance_v1.THRESHOLDS = {name: float(best[name]) for name in ["relevance", "supports", "challenges"]}
            print(f"Wrote the best thresholds into {INSTRUMENT_PATH.name} and set TUNED = True; commit it before the test run.")

    metrics = evaluate(None, reviewed, "review_weight") if len(reviewed) else evaluate(None)
    all_rows = evaluate(None)
    predicted = stance_v1.labels(scores)
    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
    predicted.to_csv(PREDICTIONS_DIR / f"stance_v1_{args.split}.csv", index=False, encoding="utf-8")
    pd.DataFrame([{"metric": name, "value": value, "rows": "reviewed"} for name, value in metrics.items()]
                 + [{"metric": name, "value": value, "rows": "all"} for name, value in all_rows.items()]).to_csv(
        VALIDATION_DIR / f"stance_{args.split}_metrics.csv", index=False, encoding="utf-8"
    )
    checked = gate(metrics)
    (VALIDATION_DIR / f"stance_{args.split}_run.json").write_text(json.dumps({
        "split": args.split, "created_utc": datetime.now(UTC).isoformat(timespec="seconds"), "commit": head,
        "uncommitted_stance_code": bool(dirty), "tuned": stance_v1.TUNED, "thresholds": stance_v1.THRESHOLDS,
        "model": stance_v1.MODEL, "revision": stance_v1.REVISION, "posts": len(truth), "reviewed_posts": len(reviewed),
        "sources": frame["source"].value_counts().to_dict(), "gate": checked, "gate_all_rows": gate(all_rows),
    }, indent=2) + "\n", encoding="utf-8")
    print(f"{args.split}: {len(truth)} posts; accuracy {metrics['accuracy']:.3f}, macro-F1 {metrics['macro_f1']:.3f}, "
          f"F1 challenges {checked['challenges_f1']:.3f}, kappa {checked['kappa']:.3f}")
    if args.split == "test":
        print("Validity gate " + ("passed: H1-A can be tested." if checked["passed"] else
                                  "NOT passed: H1-A cannot be measured with stance_v1 (docs/hipotezy.md)."))


if __name__ == "__main__":
    main()
