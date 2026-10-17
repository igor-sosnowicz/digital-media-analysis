"""Join the drawn sample with the full data of every unit: one CSV per platform.

Each file holds `unit_id`, every column of the raw download for the sampled
units and then the sampling columns from the manifest. Reddit: the row of
`data/raw/reddit_frame/`, including `day_weight`. Wikipedia: page, page URL,
revision number, timestamp, edit summary and the full article text after the
edit (`new_content`, with its length in `content_chars`). The files go to
`data_samples/`, which is tracked by git, so the team shares one copy of the sample.
"""

from datetime import datetime
from pathlib import Path

import pandas as pd

from digital_media_analysis import gold
from digital_media_analysis.paths import SAMPLES_DIR

SAMPLING_COLUMNS = ["year", "phase", "split", "order", "stratum", "signal", "N_h", "n_h", "weight"]
FILE_NAMES = {"reddit": "reddit_sample.csv", "wikipedia": "wikipedia_sample.csv"}
# A byte order mark makes Excel read the files as UTF-8, so Polish letters show correctly.
CSV_ENCODING = "utf-8-sig"


def wikipedia_keys(manifest: pd.DataFrame) -> set[tuple[str, int]]:
    """(page, revision_number) of every sampled Wikipedia unit, for `datasets.load_wikipedia_revisions`."""
    unit_ids = manifest.loc[manifest["platform"].eq("wikipedia"), "unit_id"]
    return {(page, int(number)) for page, number in unit_ids.str.rsplit("#", n=1)}


def reddit_sample(manifest: pd.DataFrame, posts: pd.DataFrame) -> pd.DataFrame:
    """Sampled Reddit posts with every raw column, then the sampling columns."""
    full = posts.assign(unit_id=posts["id"], introduced=posts["created_at_utc"])
    return _join(manifest, "reddit", full, raw_columns=list(posts.columns))


def wikipedia_sample(manifest: pd.DataFrame, revisions: pd.DataFrame) -> pd.DataFrame:
    """Sampled Wikipedia revisions with every raw field and the article length, then the sampling columns.

    `revisions` must come from `load_wikipedia_revisions(with_content=wikipedia_keys(manifest))`.
    """
    if "new_content" not in revisions:
        raise ValueError("Load the revisions with `with_content=wikipedia_keys(manifest)` to export the article text.")
    full = revisions.assign(
        unit_id=revisions["page"] + "#" + revisions["revision_number"].astype(str),
        content_chars=revisions["new_content"].str.len(),
    )
    return _join(manifest, "wikipedia", full, raw_columns=[*revisions.columns, "content_chars"])


def _join(manifest: pd.DataFrame, platform: str, full: pd.DataFrame, raw_columns: list[str]) -> pd.DataFrame:
    rows = manifest[manifest["platform"].eq(platform)]
    # Fails when a sampled unit is missing from the local data or its timestamp changed.
    joined = gold.attach_units(rows, full)
    joined = joined.sort_values(["year", "introduced", "unit_id"], ignore_index=True)
    return joined[["unit_id", *raw_columns, *SAMPLING_COLUMNS]]


def check_snapshot(design: dict, platform: str, units: pd.DataFrame) -> None:
    """Fail unless `units` hold the same population the sample was drawn from (see `sample_design.json`)."""
    period = design["study_period"][platform]
    start, end = (datetime.fromisoformat(period[key]) for key in ("start", "end"))
    current = gold.population_fingerprint(gold.in_study_period(units, start, end))
    expected = design["population"][platform]
    if current != expected:
        raise ValueError(
            f"The local {platform} data is not the snapshot the sample was drawn from: "
            f"{current['units']} units now, {expected['units']} when drawn (or the same count with other units)."
        )


def write_samples(samples: dict[str, pd.DataFrame], output_dir: Path = SAMPLES_DIR) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for platform, sample in samples.items():
        paths[platform] = output_dir / FILE_NAMES[platform]
        sample.to_csv(paths[platform], index=False, encoding=CSV_ENCODING)
    return paths
