"""Run every instrument on the same units and return document labels in codebook space.

The model instruments and refs_v1 have a raw step (`score`: model output or
reference counts, slow, cached outside git in `data/model_cache/`) and a
labelling step (thresholds and mapping, fast), so tuning reuses the raw step.
The rule instruments label directly. The frozen v1 runs through an adapter that
feeds it the columns its notebook code expected, without changing its rules.
"""

from pathlib import Path

import pandas as pd

from digital_media_analysis.instruments import gliner_v1, refs_v1, rules_v1, rules_v2, zeroshot_v1
from digital_media_analysis.instruments.labels import to_document_labels
from digital_media_analysis.paths import MODEL_CACHE_DIR

INSTRUMENTS = ["rules_v1", "zeroshot_v1", "gliner_v1", "rules_v2", "refs_v1"]
# Instruments with a raw step, by its function.
RAW_STEP = {"zeroshot_v1": zeroshot_v1.score, "gliner_v1": gliner_v1.score, "refs_v1": refs_v1.score}
LABEL_COLUMNS = ["unit_id", "platform", "cites_source", "source_types", "edit_about_sources"]


def rules_v1_labels(units: pd.DataFrame) -> pd.DataFrame:
    """Instrument v1 on the units, as in the EDA notebooks: Reddit reads only the post body, Wikipedia the edit summary."""
    parts = []
    reddit = units[units["platform"].eq("reddit")].reset_index(drop=True)
    if len(reddit):
        frame = pd.DataFrame({"subreddit": reddit["group"], "score": 0, "num_comments": 0, "text": reddit["text"].fillna("")})
        mentions = rules_v1.extract_reddit_references(frame)
        labels = to_document_labels(
            mentions, frame.reset_index(names="row_index"), ["row_index"], "category",
            rules_v1.REDDIT_CATEGORY_MAP, rules_v1.REDDIT_NON_CITATION,
        )
        parts.append(labels.assign(unit_id=reddit["unit_id"].astype(str).to_numpy()[labels["row_index"]], platform="reddit"))
    wikipedia = units[units["platform"].eq("wikipedia")].reset_index(drop=True)
    if len(wikipedia):
        key = wikipedia["unit_id"].astype(str).str.rsplit("#", n=1, expand=True)
        frame = pd.DataFrame({"page": key[0], "revision_number": key[1].astype(int), "comment": wikipedia["text"].fillna("")})
        mentions = rules_v1.extract_wikipedia_references(frame)
        labels = to_document_labels(
            mentions, frame, ["page", "revision_number"], "source_category",
            rules_v1.WIKIPEDIA_CATEGORY_MAP, rules_v1.WIKIPEDIA_NON_CITATION,
        )
        parts.append(labels.assign(unit_id=labels["page"] + "#" + labels["revision_number"].astype(str), platform="wikipedia"))
    # v1 does not measure edit_about_sources.
    return pd.concat(parts, ignore_index=True).assign(edit_about_sources=pd.NA)[LABEL_COLUMNS]


def raw_output(name: str, units: pd.DataFrame, tag: str, cache_dir: Path = MODEL_CACHE_DIR, refresh: bool = False) -> pd.DataFrame:
    """Raw output of an instrument for `units`, read from `<cache_dir>/<name>_<tag>.csv` when it covers them."""
    score = RAW_STEP[name]
    path = cache_dir / f"{name}_{tag}.csv"
    wanted = set(units["unit_id"].astype(str))
    if path.exists() and not refresh:
        cached = pd.read_csv(path, dtype={"unit_id": str}, keep_default_na=False)
        meta = path.with_suffix(".units")
        if meta.exists() and set(meta.read_text(encoding="utf-8").split("\n")) - {""} == wanted:
            return cached
    output = score(units)
    path.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(path, index=False, encoding="utf-8")
    path.with_suffix(".units").write_text("\n".join(sorted(wanted)), encoding="utf-8")
    return output


def document_labels(name: str, units: pd.DataFrame, raw: pd.DataFrame | None = None, **settings) -> pd.DataFrame:
    """Labels of one instrument; `raw` is its cached model output, `settings` override frozen thresholds (tuning)."""
    if name == "rules_v1":
        return rules_v1_labels(units)
    if name == "zeroshot_v1":
        return zeroshot_v1.labels(raw, **settings)[LABEL_COLUMNS]
    if name == "gliner_v1":
        return gliner_v1.labels(raw, units, **settings)[LABEL_COLUMNS]
    if name == "rules_v2":
        return rules_v2.labels(units)[LABEL_COLUMNS]
    if name == "refs_v1":
        return refs_v1.labels(raw, **settings)[LABEL_COLUMNS]
    raise ValueError(f"Unknown instrument {name!r}; choose from {INSTRUMENTS}.")
