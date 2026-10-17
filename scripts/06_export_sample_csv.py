"""Write the drawn sample with the full data of every unit to `data_samples/`, one CSV per platform.

Checks first that the local data is the snapshot the sample was drawn from and
that each file has the number of units the design asked for.
"""

import json

from digital_media_analysis import datasets, gold, sample_export
from digital_media_analysis.paths import RAW_REDDIT_FRAME_DIR


def main() -> None:
    manifest = gold.load_manifest()
    design = json.loads(gold.DESIGN_PATH.read_text(encoding="utf-8"))

    posts = datasets.load_reddit_posts(RAW_REDDIT_FRAME_DIR)
    revisions = datasets.load_wikipedia_revisions(with_content=sample_export.wikipedia_keys(manifest))
    sample_export.check_snapshot(design, "reddit", gold.reddit_units(posts))
    sample_export.check_snapshot(design, "wikipedia", gold.wikipedia_units(revisions))

    samples = {
        "reddit": sample_export.reddit_sample(manifest, posts),
        "wikipedia": sample_export.wikipedia_sample(manifest, revisions),
    }
    for platform, sample in samples.items():
        expected = design["allocation"][platform]["total"]
        if len(sample) != expected:
            raise SystemExit(f"{platform}: {len(sample)} units in the manifest, the design asks for {expected}.")

    paths = sample_export.write_samples(samples)
    for platform, sample in samples.items():
        per_year = sample.groupby("year").size()
        print(f"{paths[platform]}: {len(sample)} rows, {len(sample.columns)} columns, {len(per_year)} years")
        print("  " + ", ".join(f"{year}: {n}" for year, n in per_year.items()))


if __name__ == "__main__":
    main()
