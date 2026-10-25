"""Draw the H1 analysis sample from the Reddit frame and label it with the frozen instruments.

The sample takes at most `hypotheses.h1.posts_per_subreddit_year` posts of each
subreddit and year in `hypotheses.h1.subreddits` (config.yaml) over the
sensitivity period, with weights back to the frame (docs/hipotezy.md). Writes:
- annotations/hypotheses/h1_sample.csv: post IDs, subreddit, year, day, weights;
- annotations/frame_labels/h1_gliner_v1.csv: source labels (H1-B);
- annotations/frame_labels/h1_stance_v1.csv: stances (H1-A), only once stance_v1 is tuned;
  its raw scores are cached in data/model_cache/ either way.
`--audit-annotators` also exports a workbook per annotator for the audit of rare
source categories (annotations/sheets/audit_<annotator>.xlsx) and its sample.
Needs the `ml` dependency group. This is measurement only: no hypothesis is tested here.
"""

import argparse
import json

import numpy as np
import pandas as pd

from digital_media_analysis import gold, hypotheses
from digital_media_analysis.annotation_sheets import write_workbook
from digital_media_analysis.codebook import load_codebook
from digital_media_analysis.config_reader import get_hypotheses
from digital_media_analysis.instruments import runner, stance_v1
from digital_media_analysis.paths import FRAME_LABELS_DIR, HYPOTHESES_DIR, MODEL_CACHE_DIR, SHEETS_DIR, VALIDATION_DIR

# Audit strata by predicted category, in priority order; the rest forms the last stratum.
AUDIT_STRATA = ["scientific", "institutional", "unknown", "personal", "other"]


def audit_sample(labels: pd.DataFrame, per_stratum: int, seed: int) -> pd.DataFrame:
    """Posts per predicted category (first match in AUDIT_STRATA, else `rest`), with inclusion probabilities."""
    def stratum(source_types: str) -> str:
        codes = set(str(source_types).split(";"))
        return next((code for code in AUDIT_STRATA if code in codes), "rest")

    frame = labels.assign(stratum=labels["source_types"].map(stratum))
    rng = np.random.default_rng(seed)
    parts = []
    for name, group in frame.groupby("stratum"):
        chosen = group if len(group) <= per_stratum else group.sample(n=per_stratum, random_state=rng)
        parts.append(chosen.assign(inclusion=len(chosen) / len(group), stratum_size=len(group)))
    audit = pd.concat(parts, ignore_index=True)
    return audit.assign(order=rng.permutation(len(audit)) + 1).sort_values("order", ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Recompute model output instead of reading the cache.")
    parser.add_argument("--audit-annotators", nargs="+", default=[], help="Export an audit workbook for each annotator.")
    parser.add_argument("--audit-per-stratum", type=int, default=30)
    parser.add_argument("--force", action="store_true", help="Overwrite existing audit workbooks.")
    args = parser.parse_args()

    settings = get_hypotheses()["h1"]
    frame = gold.reddit_units(gold.load_reddit_frame())
    sample = hypotheses.h1_analysis_sample(
        frame, settings["subreddits"], settings["sensitivity_period"], settings["posts_per_subreddit_year"]
    )
    HYPOTHESES_DIR.mkdir(parents=True, exist_ok=True)
    FRAME_LABELS_DIR.mkdir(parents=True, exist_ok=True)
    sample.to_csv(HYPOTHESES_DIR / "h1_sample.csv", index=False, encoding="utf-8")
    print(f"H1 sample: {len(sample)} posts in {sample.groupby(['group', 'year']).ngroups} subreddit-years")

    units = frame[frame["unit_id"].isin(sample["unit_id"])].reset_index(drop=True)
    raw = runner.raw_output("gliner_v1", units, "h1", refresh=args.refresh)
    labels = runner.document_labels("gliner_v1", units, raw)
    labels.to_csv(FRAME_LABELS_DIR / "h1_gliner_v1.csv", index=False, encoding="utf-8")
    print(f"gliner_v1 labels: {len(labels)} posts -> {FRAME_LABELS_DIR / 'h1_gliner_v1.csv'}")

    if args.audit_annotators:
        audit = audit_sample(labels, args.audit_per_stratum, hypotheses.SEED)
        audit.merge(sample[["unit_id", "group", "year"]], on="unit_id").to_csv(
            HYPOTHESES_DIR / "h1_audit_sample.csv", index=False, encoding="utf-8"
        )
        audit_units = units.set_index("unit_id").loc[audit["unit_id"]].reset_index()
        codebook = load_codebook()
        for annotator in args.audit_annotators:
            path = SHEETS_DIR / f"audit_{annotator}.xlsx"
            if path.exists() and not args.force:
                parser.error(f"{path} exists and may hold labels; use --force to overwrite.")
            write_workbook(path, annotator, "audit", {"reddit": audit_units}, codebook)
            print(f"Wrote {path} ({len(audit_units)} posts; strata {audit['stratum'].value_counts().to_dict()})")

    # Last, as it is the slowest step (three NLI hypotheses per post on a CPU).
    scores = hypotheses.cached_scores(MODEL_CACHE_DIR / "stance_v1_h1.csv", units, stance_v1.score, refresh=args.refresh)
    test_run = VALIDATION_DIR / "stance_test_run.json"
    passed = json.loads(test_run.read_text(encoding="utf-8")).get("gate", {}).get("passed", False) if test_run.exists() else False
    if stance_v1.TUNED and passed:
        stances = stance_v1.labels(scores)
        stances.to_csv(FRAME_LABELS_DIR / "h1_stance_v1.csv", index=False, encoding="utf-8")
        print(f"stance_v1 labels: {len(stances)} posts -> {FRAME_LABELS_DIR / 'h1_stance_v1.csv'}")
    elif stance_v1.TUNED and test_run.exists():
        print("stance_v1 did not pass the validity gate on the test split: no stance labels written; "
              "H1-A cannot be measured with this instrument (docs/hipotezy.md).")
    else:
        print("stance_v1 is not tuned and tested yet: scores cached, no stance labels written (scripts/07b).")


if __name__ == "__main__":
    main()
