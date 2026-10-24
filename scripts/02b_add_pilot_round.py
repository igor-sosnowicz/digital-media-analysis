"""Draw another pilot round from units outside the sample and append it to the manifest.

The new units get phase `pilot` and the next free split name (`pilot2`, then
`pilot3`, ...), so they join the pilot workbooks but never dev or test. Existing
manifest rows do not change. Afterwards re-export the CSVs (`make sample-csv`) and
the pilot workbooks of everyone who codes the new round.
"""

import argparse
import json
from datetime import UTC, datetime

import pandas as pd

from digital_media_analysis import gold, sample_export


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reddit", type=int, default=0, help="Reddit posts in the new round.")
    parser.add_argument("--wikipedia", type=int, default=0, help="Wikipedia edit summaries in the new round.")
    args = parser.parse_args()
    counts = {"reddit": args.reddit, "wikipedia": args.wikipedia}
    if any(count < 0 for count in counts.values()) or not any(counts.values()):
        parser.error("Give a positive --reddit and/or --wikipedia.")

    manifest = gold.load_manifest()
    design = json.loads(gold.DESIGN_PATH.read_text(encoding="utf-8"))
    reddit, wikipedia = gold.load_units()
    units = {"reddit": reddit, "wikipedia": wikipedia}
    for platform, platform_units in units.items():
        sample_export.check_snapshot(design, platform, platform_units)

    split = gold.next_pilot_round(manifest)
    rows = gold.draw_pilot_round(manifest, units, counts, split, seed=design["seed"])
    manifest = pd.concat([manifest, rows], ignore_index=True)
    manifest = manifest.sort_values(["platform", "split", "order"], ignore_index=True)

    design.setdefault("pilot_rounds", {})[split] = {
        "created_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "counts": counts,
        "frame": "units of the sampling frame in none of the earlier splits",
        "per_year": {
            platform: {str(year): int(n) for year, n in part.groupby("year").size().items()}
            for platform, part in rows.groupby("platform")
        },
    }
    design["sample_sizes"] = {
        platform: frame["split"].value_counts().sort_index().to_dict() for platform, frame in manifest.groupby("platform")
    }
    gold.save_sample(manifest, design, force=True)

    for platform, part in rows.groupby("platform"):
        per_year = part.groupby("year").size()
        print(f"{platform} {split}: {len(part)} units, {len(per_year)} years ({', '.join(f'{y}: {n}' for y, n in per_year.items())})")
    print(f"Appended to {gold.MANIFEST_PATH}; now re-export the CSVs and the pilot workbooks.")


if __name__ == "__main__":
    main()
