"""Error analysis of the instruments (slide 3): errors with causes, a Pareto chart and differential error.

Writes:
- annotations/errors/<split>_errors.csv: every error of the chosen instruments on
  the gold units of `--split` (default dev), text-free, with a suggested cause
  and the cause a person confirmed;
- annotations/sheets/errors_<split>.xlsx: the same errors with the unit text, to
  confirm the causes; `--import` reads it back into the CSV;
- annotations/errors/<split>_pareto.csv and .png: errors per cause;
- annotations/errors/differential_<split>.csv: error rates of `cites_source` by
  period, subreddit or page for every instrument with predictions of
  `--differential-split` (default test; `all` joins dev and test, as for the
  untuned v1).
Uses saved predictions (annotations/predictions/, from scripts/07_validate_instruments.py) only.
"""

import argparse
import sys

import matplotlib

matplotlib.use("Agg")

import pandas as pd  # noqa: E402

from digital_media_analysis import adjudication, annotations, errors, gold, validation  # noqa: E402
from digital_media_analysis.codebook import load_codebook  # noqa: E402
from digital_media_analysis.config_reader import get_hypotheses  # noqa: E402
from digital_media_analysis.instruments import runner  # noqa: E402
from digital_media_analysis.paths import ERRORS_DIR, PREDICTIONS_DIR, SHEETS_DIR  # noqa: E402

# Halves of each platform's study period, for differential error over time.
PERIODS = {"reddit": (2012, "2005–2012", "2013–2020"), "wikipedia": (2022, "2020–2022", "2023–2026")}


def predictions(instrument: str, splits: list[str]) -> pd.DataFrame | None:
    paths = [PREDICTIONS_DIR / f"{instrument}_{split}.csv" for split in splits]
    if not all(path.exists() for path in paths):
        return None
    frames = [pd.read_csv(path, dtype={"unit_id": str, "source_types": str}) for path in paths]
    return pd.concat(frames, ignore_index=True).astype({"cites_source": "Int64", "edit_about_sources": "Int64"})


def with_groups(frame: pd.DataFrame, manifest: pd.DataFrame, units: pd.DataFrame) -> pd.DataFrame:
    """Paired labels with the grouping columns: period, and subreddit (Polish ones together) or page."""
    english = {name.casefold() for name in get_hypotheses()["h1"]["subreddits"]}
    frame = frame.merge(manifest[["unit_id", "platform", "year"]].astype({"unit_id": str}), on=["unit_id", "platform"])
    frame = frame.merge(units[["unit_id", "platform", "group"]].astype({"unit_id": str}), on=["unit_id", "platform"])
    period = [PERIODS[platform][1] if year <= PERIODS[platform][0] else PERIODS[platform][2]
              for platform, year in zip(frame["platform"], frame["year"])]
    source = [group if platform == "wikipedia" or group.casefold() in english else "polskie subreddity"
              for platform, group in zip(frame["platform"], frame["group"])]
    return frame.assign(period=period, source=source)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=["dev", "test"], default="dev", help="Split of the error list and Pareto chart.")
    parser.add_argument("--instruments", nargs="+", choices=runner.INSTRUMENTS, default=["rules_v1", "gliner_v1", "rules_v2", "refs_v1"])
    parser.add_argument("--differential-split", choices=["dev", "test", "all"], default="test")
    parser.add_argument("--import", dest="import_", action="store_true", help="Read confirmed causes from the review workbook.")
    parser.add_argument("--force", action="store_true", help="Overwrite the review workbook (it may hold confirmed causes).")
    parser.add_argument("--samples", type=int, default=validation.BOOTSTRAP_SAMPLES, help="Bootstrap replicates.")
    args = parser.parse_args()

    codes = load_codebook().category_codes
    manifest = gold.load_manifest()
    reference, _ = annotations.gold_reference(annotations.load_labels("gold"), adjudication.load_decisions("gold"))
    reference = reference.merge(manifest[["unit_id", "platform", "split"]], on=["unit_id", "platform"])
    reddit, wikipedia = gold.load_units()
    units = pd.concat([reddit, wikipedia], ignore_index=True)
    ERRORS_DIR.mkdir(parents=True, exist_ok=True)

    errors_path = ERRORS_DIR / f"{args.split}_errors.csv"
    review_path = SHEETS_DIR / f"errors_{args.split}.xlsx"
    if args.import_:
        if not (errors_path.exists() and review_path.exists()):
            sys.exit(f"Export the errors first (without --import): {errors_path.name}, {review_path.name}.")
        table, problems = errors.read_review(review_path, pd.read_csv(errors_path, dtype=str, keep_default_na=False))
        if problems:
            print("\n".join(f"  - {problem}" for problem in problems[:20]))
            sys.exit("Fix the causes above in the review workbook and import it again.")
    else:
        parts = []
        split_reference = reference[reference["split"].eq(args.split)]
        for instrument in args.instruments:
            labels = predictions(instrument, [args.split])
            if labels is None:
                print(f"{instrument}: no predictions for {args.split}; run scripts/07_validate_instruments.py first.")
                continue
            parts.append(errors.error_table(split_reference, labels, units, instrument, codes, args.split))
        table = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=errors.ERROR_COLUMNS)
        if review_path.exists() and not args.force:
            print(f"{review_path} exists and may hold confirmed causes: left as it is (use --force to overwrite).")
        else:
            errors.write_review(review_path, table, units)
            print(f"Review workbook -> {review_path}")
    table.to_csv(errors_path, index=False, encoding="utf-8")
    counted = errors.pareto(table)
    counted.to_csv(ERRORS_DIR / f"{args.split}_pareto.csv", index=False, encoding="utf-8")
    if len(counted):
        errors.plot_pareto(counted, ERRORS_DIR / f"{args.split}_pareto.png")
    for instrument, part in counted.groupby("instrument"):
        top = ", ".join(f"{row.cause} {row.errors}" for row in part.head(3).itertuples(index=False))
        print(f"{instrument}: {int(part['errors'].sum())} errors on {args.split}; most: {top}")

    splits = ["dev", "test"] if args.differential_split == "all" else [args.differential_split]
    split_reference = reference[reference["split"].isin(splits)].drop(columns="split")
    rows = []
    for instrument in runner.INSTRUMENTS:
        labels = predictions(instrument, splits)
        if labels is None:
            continue
        frame = with_groups(validation.paired(split_reference, labels, manifest), manifest, units)
        for grouping in ["period", "source"]:
            for variable in ["cites_source", "edit_about_sources"]:
                table = validation.differential_errors(frame, grouping, variable, samples=args.samples)
                rows.append(table.assign(instrument=instrument, splits="+".join(splits)))
    differential = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    differential.to_csv(ERRORS_DIR / f"differential_{args.differential_split}.csv", index=False, encoding="utf-8")
    flagged = differential[differential["p_permutation"].lt(0.05)] if len(differential) else differential
    for row in flagged.drop_duplicates(["instrument", "platform", "variable", "grouping", "rate"]).itertuples(index=False):
        print(f"differential error: {row.instrument} {row.platform} {row.variable} {row.rate} by {row.grouping} "
              f"(p = {row.p_permutation:.3f})")
    print(f"Error tables -> {ERRORS_DIR}")


if __name__ == "__main__":
    main()
