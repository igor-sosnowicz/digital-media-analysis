"""Validate instruments on the gold sample: rules v1, zero-shot NLI (zeroshot_v1) and GLiNER (gliner_v1).

Instruments are tuned on the dev split only (`--tune` writes the threshold grid;
the chosen values are then frozen in the instrument modules). The test split
runs only with `--frozen` and when the instrument and validation code is
committed, so test results always belong to a recorded commit. Labels go to
`annotations/predictions/`, metrics to `annotations/validation/`; raw model
output is cached in `data/model_cache/`. Needs the `ml` dependency group.
"""

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime

import numpy as np
import pandas as pd

from digital_media_analysis import annotations, gold, validation
from digital_media_analysis.codebook import load_codebook
from digital_media_analysis.instruments import gliner_v1, runner, zeroshot_v1
from digital_media_analysis.paths import PREDICTIONS_DIR, PROJECT_ROOT, VALIDATION_DIR

# Code that must be committed before the test split runs.
FROZEN_PATHS = ["src/digital_media_analysis/instruments", "src/digital_media_analysis/validation.py", "scripts/07_validate_instruments.py"]
GRID = [round(value, 2) for value in np.arange(0.05, 0.96, 0.05)]


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True, check=True).stdout.strip()


def tune(name: str, units: pd.DataFrame, raw: pd.DataFrame, reference: pd.DataFrame, manifest: pd.DataFrame, codes: list[str]) -> pd.DataFrame:
    """Objective on the dev split for every threshold (and hypothesis language) of an instrument.

    The choice maximises `combined`, the mean of the weighted MASI similarity and
    the `cites_source` F1. MASI alone rewards labelling every Wikipedia summary
    `none` (most of them are), which leaves no source found.
    """
    rows = []
    for platform in ["reddit", "wikipedia"]:
        platform_units = units[units["platform"].eq(platform)]
        platform_raw = raw[raw["platform"].eq(platform)]
        if name == "zeroshot_v1":
            for language in zeroshot_v1.LANGUAGES:
                for threshold in GRID:
                    labels = zeroshot_v1.labels(platform_raw, {platform: language}, {platform: threshold}, threshold)
                    scores = validation.objective(reference, labels, manifest, codes)
                    rows.append({"platform": platform, "language": language, "threshold": threshold, **scores})
        else:
            for threshold in [value for value in GRID if value >= gliner_v1.SCORE_FLOOR]:
                labels = gliner_v1.labels(platform_raw, platform_units, {platform: threshold})
                scores = validation.objective(reference, labels, manifest, codes)
                rows.append({"platform": platform, "language": "", "threshold": threshold, **scores})
    grid = pd.DataFrame(rows).assign(instrument=name)
    return grid.assign(combined=(grid["masi"] + grid["cites_f1"].fillna(0)) / 2)


def best_settings(grid: pd.DataFrame) -> pd.DataFrame:
    """Per platform, the row with the highest `combined` (ties: higher MASI, then the lower threshold)."""
    ordered = grid.sort_values(["combined", "masi", "threshold"], ascending=[False, False, True])
    return ordered.groupby("platform").head(1)


def settings() -> dict:
    """The frozen choices of every instrument, recorded with each run."""
    return {
        "zeroshot_v1": {"model": zeroshot_v1.MODEL, "revision": zeroshot_v1.REVISION, "language": zeroshot_v1.LANGUAGE,
                        "thresholds": zeroshot_v1.THRESHOLDS, "edit_threshold": zeroshot_v1.EDIT_THRESHOLD},
        "gliner_v1": {"model": gliner_v1.MODEL, "revision": gliner_v1.REVISION, "thresholds": gliner_v1.THRESHOLDS},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=["dev", "test"], default="dev")
    parser.add_argument("--instruments", nargs="+", choices=runner.INSTRUMENTS, default=runner.INSTRUMENTS)
    parser.add_argument("--samples", type=int, default=validation.BOOTSTRAP_SAMPLES, help="Bootstrap replicates.")
    parser.add_argument("--tune", action="store_true", help="Dev only: write the threshold grid of the model instruments.")
    parser.add_argument("--frozen", action="store_true", help="Required for the test split: the instruments are final.")
    parser.add_argument("--refresh", action="store_true", help="Recompute model output instead of reading the cache.")
    args = parser.parse_args()

    head = git("rev-parse", "HEAD")
    dirty = git("status", "--porcelain", "--", *FROZEN_PATHS)
    if args.split == "test":
        if args.tune:
            parser.error("Tuning on the test split is not allowed.")
        if not args.frozen:
            parser.error("The test split runs once, on frozen instruments: commit them and pass --frozen.")
        if dirty:
            sys.exit(f"Commit the instrument and validation code before the test run:\n{dirty}")

    codes = load_codebook().category_codes
    manifest = gold.load_manifest()
    reference, conflicts = annotations.gold_reference(annotations.load_labels("gold"))
    if len(conflicts):
        print(f"{conflicts['unit_id'].nunique()} units coded differently by several people are left out until adjudicated.")
    reference = reference.merge(manifest[["unit_id", "platform", "split"]], on=["unit_id", "platform"])
    reference = reference[reference["split"].eq(args.split)].drop(columns="split")
    reddit, wikipedia = gold.load_units()
    units = pd.concat([reddit, wikipedia], ignore_index=True)
    units = units.merge(reference[["unit_id", "platform"]], on=["unit_id", "platform"])
    print(f"{args.split}: {len(units)} gold units ({units['platform'].value_counts().to_dict()})")

    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    tables, confusions = [], []
    for name in args.instruments:
        raw = None if name == "rules_v1" else runner.raw_output(name, units, args.split, refresh=args.refresh)
        if args.tune and raw is not None:
            if args.split != "dev":
                parser.error("--tune works on the dev split only.")
            grid = tune(name, units, raw, reference, manifest, codes)
            grid.to_csv(VALIDATION_DIR / f"dev_tuning_{name}.csv", index=False, encoding="utf-8")
            best = best_settings(grid)
            print(f"{name} best on dev (mean of MASI and cites_source F1):\n{best.round(3).to_string(index=False)}")
            if name == "zeroshot_v1":
                language = best.loc[best["platform"].eq("wikipedia"), "language"].iloc[0]
                edit = grid[grid["platform"].eq("wikipedia") & grid["language"].eq(language)]
                edit = edit.sort_values(["edit_f1", "threshold"], ascending=[False, True]).head(1)
                print(f"{name} edit_about_sources threshold on dev (F1, language {language}):\n{edit.round(3).to_string(index=False)}")
        labels = runner.document_labels(name, units, raw)
        labels.to_csv(PREDICTIONS_DIR / f"{name}_{args.split}.csv", index=False, encoding="utf-8")
        tables.append(validation.evaluate(reference, labels, manifest, name, codes, samples=args.samples))
        confusions.append(validation.confusion(reference, labels, manifest, name))

    table = pd.concat(tables, ignore_index=True)
    table.to_csv(VALIDATION_DIR / f"{args.split}_metrics.csv", index=False, encoding="utf-8")
    pd.concat(confusions, ignore_index=True).to_csv(VALIDATION_DIR / f"{args.split}_confusion.csv", index=False, encoding="utf-8")
    run = {
        "split": args.split, "created_utc": datetime.now(UTC).isoformat(timespec="seconds"), "commit": head,
        "uncommitted_instrument_code": bool(dirty), "instruments": args.instruments, "settings": settings(),
        "units": units["platform"].value_counts().to_dict(), "bootstrap_samples": args.samples,
    }
    (VALIDATION_DIR / f"{args.split}_run.json").write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")

    headline = table[table["subset"].eq("all") & (
        (table["variable"].isin(validation.BINARY) & table["metric"].eq("f1"))
        | (table["variable"].eq("source_types") & table["metric"].isin(["masi", "macro_f1"]))
    )]
    for row in headline.itertuples(index=False):
        interval = f"[{row.low:.2f}, {row.high:.2f}]" if not np.isnan(row.low) else ""
        print(f"{row.platform:<10} {row.instrument:<12} {row.variable:<19} {row.metric:<9} {row.value:.3f} {interval}")
    print(f"Metrics, confusion counts and run settings written to {VALIDATION_DIR}")


if __name__ == "__main__":
    main()
