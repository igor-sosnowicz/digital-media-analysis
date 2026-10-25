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
from digital_media_analysis.paths import MODEL_CACHE_DIR, PREDICTIONS_DIR, PROJECT_ROOT, VALIDATION_DIR

FROZEN_PATHS = ["src/digital_media_analysis/instruments/stance_v1.py", "src/digital_media_analysis/instruments/nli.py",
                "src/digital_media_analysis/validation.py", "scripts/07b_validate_stance.py"]
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
    reference, conflicts = stance.reference(stance.load_labels("gold"))
    if reference.empty:
        sys.exit("No stance labels of the gold phase yet: export stance sheets (03b), code them, import them (04b).")
    if len(conflicts):
        print(f"{conflicts['unit_id'].nunique()} posts with different stances are left out until adjudicated.")
    reference = reference.merge(manifest[["unit_id", "platform", "split"]], on=["unit_id", "platform"])
    reference = reference[reference["split"].eq(args.split)]
    reddit, _ = gold.load_units()
    units = reddit[reddit["unit_id"].isin(reference["unit_id"])].reset_index(drop=True)
    scores = hypotheses.cached_scores(MODEL_CACHE_DIR / f"stance_v1_{args.split}.csv", units, stance_v1.score, refresh=args.refresh)
    weights = validation.design_weights(reference[["unit_id", "platform"]], manifest).set_index("unit_id")["weight"]
    truth = reference.set_index("unit_id")[stance.STANCE]

    def evaluate(thresholds: dict[str, float] | None) -> dict[str, float]:
        predicted = stance_v1.labels(scores, thresholds).set_index("unit_id")[stance.STANCE]
        return validation.nominal_metrics(truth, predicted.loc[truth.index], weights.loc[truth.index], classes)

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

    metrics = evaluate(None)
    predicted = stance_v1.labels(scores)
    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
    predicted.to_csv(PREDICTIONS_DIR / f"stance_v1_{args.split}.csv", index=False, encoding="utf-8")
    pd.DataFrame([{"metric": name, "value": value} for name, value in metrics.items()]).to_csv(
        VALIDATION_DIR / f"stance_{args.split}_metrics.csv", index=False, encoding="utf-8"
    )
    checked = gate(metrics)
    (VALIDATION_DIR / f"stance_{args.split}_run.json").write_text(json.dumps({
        "split": args.split, "created_utc": datetime.now(UTC).isoformat(timespec="seconds"), "commit": head,
        "uncommitted_stance_code": bool(dirty), "tuned": stance_v1.TUNED, "thresholds": stance_v1.THRESHOLDS,
        "model": stance_v1.MODEL, "revision": stance_v1.REVISION, "posts": len(truth), "gate": checked,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"{args.split}: {len(truth)} posts; accuracy {metrics['accuracy']:.3f}, macro-F1 {metrics['macro_f1']:.3f}, "
          f"F1 challenges {checked['challenges_f1']:.3f}, kappa {checked['kappa']:.3f}")
    if args.split == "test":
        print("Validity gate " + ("passed: H1-A can be tested." if checked["passed"] else
                                  "NOT passed: H1-A cannot be measured with stance_v1 (docs/hipotezy.md)."))


if __name__ == "__main__":
    main()
