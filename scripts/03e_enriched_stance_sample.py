"""Draw the enriched r/conspiracy sample for the stance reference and export its workbooks (plan B).

The gold sample has very few posts challenging the scientific consensus, so the
validity gate of H1-A would rest on a handful of posts. This sample adds
r/conspiracy posts of the H1 analysis sample, outside the gold manifest, in
three strata (docs/hipotezy.md, amendment of 26.10.2026): a consensus topic
(topics_v1, all posts), a science term (150) and the rest (60). Each post's
weight is 1 / its inclusion probability; half of each stratum is dev, half test.
The draw uses neither stance_v1 nor any LLM label. Writes
annotations/hypotheses/stance_enriched_sample.csv and one blind workbook per
annotator (stance_enriched_<annotator>.xlsx) in --out-dir.
"""

import argparse
from pathlib import Path

import pandas as pd

from digital_media_analysis import gold, stance, topics
from digital_media_analysis.codebook import load_codebook
from digital_media_analysis.paths import HYPOTHESES_DIR, SHEETS_DIR

SAMPLE_PATH = HYPOTHESES_DIR / "stance_enriched_sample.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotators", nargs="+", default=["IS", "JP"])
    parser.add_argument("--out-dir", type=Path, default=SHEETS_DIR / "llm", help="Where to write the workbooks.")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing sample and workbooks.")
    args = parser.parse_args()
    if SAMPLE_PATH.exists() and not args.force:
        parser.error(f"{SAMPLE_PATH} exists; the sample is drawn once (use --force only before any labelling).")

    h1 = pd.read_csv(HYPOTHESES_DIR / "h1_sample.csv", dtype={"unit_id": str})
    frame = gold.reddit_units(gold.load_reddit_frame())
    manifest_ids = set(gold.load_manifest()["unit_id"].astype(str))
    units = frame[frame["unit_id"].isin(h1.loc[h1["group"].eq("conspiracy"), "unit_id"]) & ~frame["unit_id"].isin(manifest_ids)]
    units = units.sort_values("unit_id").reset_index(drop=True)
    found = topics.label((units["title"].fillna("") + " " + units["text"].fillna("")).set_axis(units["unit_id"]))
    sample = stance.draw_enriched(units, found["consensus_topic"].reset_index(drop=True), annotators=args.annotators)
    columns = ["unit_id", "group", "year", "stratum", "stratum_size", "inclusion", "split", "annotator", "order"]
    HYPOTHESES_DIR.mkdir(parents=True, exist_ok=True)
    sample[columns].to_csv(SAMPLE_PATH, index=False, encoding="utf-8")
    print(f"{len(sample)} posts -> {SAMPLE_PATH}")
    print(sample.groupby(["stratum", "split"]).size().unstack(fill_value=0).to_string())

    codebook = load_codebook()
    for annotator in args.annotators:
        path = stance.workbook_path(stance.ENRICHED_PHASE, annotator, args.out_dir)
        if path.exists() and not args.force:
            parser.error(f"{path} exists and may hold labels; use --force to overwrite.")
        part = sample[sample["annotator"].eq(annotator)].reset_index(drop=True)
        stance.write_workbook(path, annotator, stance.ENRICHED_PHASE, part, codebook)
        print(f"Wrote {path} ({len(part)} posts)")


if __name__ == "__main__":
    main()
