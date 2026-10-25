"""Instrument GLiNER v1: zero-shot extraction of source mentions, mapped onto codebook categories.

A multilingual GLiNER model finds spans of the unit text that match entity
labels given in words ("news outlet", "scientific journal", ...). Every label
maps to one codebook category (`ENTITY_LABELS`), so the spans a unit keeps above
the platform's threshold give its `source_types`. A link that no kept span
types still cites an identified source, which the codebook files under `other`
(rule R7), as `instruments.labels.UNTYPED_SOURCE`. The instrument does not
measure `edit_about_sources`.

`score` keeps every span above `SCORE_FLOOR`; the thresholds were chosen on the
dev split only (`scripts/07_validate_instruments.py --tune`) and are frozen with
the commit that runs the test split.
"""

import re

import pandas as pd

from digital_media_analysis.codebook import NO_SOURCE
from digital_media_analysis.instruments.labels import LABEL_SEPARATOR, UNTYPED_SOURCE
from digital_media_analysis.instruments.unit_text import unit_texts

VERSION = "gliner_v1"
MODEL = "urchade/gliner_multi-v2.1"
REVISION = "443d26d654e0324125a96bebd8e796c14ff2efe6"

# Entity label given to the model -> codebook category.
ENTITY_LABELS = {
    "scientific journal or research paper": "scientific",
    "university or research institute": "institutional",
    "health organization": "institutional",
    "statistics office": "institutional",
    "news outlet or newspaper": "media",
    "magazine": "media",
    "personal experience": "personal",
    "social media platform": "social_blog",
    "video platform": "social_blog",
    "blog": "social_blog",
    "encyclopedia or dictionary": "encyclopedia",
    "company or online shop": "other",
    "government agency or office": "other",
    "law or regulation": "other",
    "non-governmental organization": "other",
    "unnamed source such as studies or experts": "unknown",
}
URL = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
SCORE_FLOOR = 0.2

# Chosen on the dev split on 24.10.2026 (`scripts/07_validate_instruments.py --tune`):
# highest mean of weighted MASI and cites_source F1. The Reddit choice is the
# lowest score kept (`SCORE_FLOOR`).
THRESHOLDS = {"reddit": 0.2, "wikipedia": 0.85}


def score(units: pd.DataFrame) -> pd.DataFrame:
    """Spans above `SCORE_FLOOR`: unit_id, platform, label, category, span, score (one row per span)."""
    from gliner import GLiNER

    model = GLiNER.from_pretrained(MODEL, revision=REVISION)
    texts = unit_texts(units)
    rows = []
    for unit_id, platform in zip(units["unit_id"].astype(str), units["platform"]):
        for entity in model.predict_entities(texts[unit_id], list(ENTITY_LABELS), threshold=SCORE_FLOOR):
            rows.append({
                "unit_id": unit_id,
                "platform": platform,
                "label": entity["label"],
                "category": ENTITY_LABELS[entity["label"]],
                "span": entity["text"],
                "score": float(entity["score"]),
            })
    return pd.DataFrame(rows, columns=["unit_id", "platform", "label", "category", "span", "score"])


def has_link(units: pd.DataFrame) -> pd.Series:
    """Whether the instrument input of a unit holds a link (the post link or a URL in the text)."""
    texts = unit_texts(units)
    return texts.map(lambda text: bool(URL.search(text)) or "\nLink: " in f"\n{text}")


def labels(spans: pd.DataFrame, units: pd.DataFrame, thresholds: dict[str, float] | None = None) -> pd.DataFrame:
    """Document labels: unit_id, platform, cites_source, source_types, edit_about_sources (always missing)."""
    thresholds = thresholds or THRESHOLDS
    linked = has_link(units)
    kept = spans[spans["score"] >= spans["platform"].map(thresholds)]
    found = kept.groupby("unit_id")["category"].agg(lambda codes: sorted(set(codes)))
    rows = []
    for unit_id, platform in zip(units["unit_id"].astype(str), units["platform"]):
        codes = list(found.get(unit_id, []))
        if not codes and linked[unit_id]:
            codes = [UNTYPED_SOURCE]
        rows.append({
            "unit_id": unit_id,
            "platform": platform,
            "cites_source": int(bool(codes)),
            "source_types": LABEL_SEPARATOR.join(codes) or NO_SOURCE,
            "edit_about_sources": pd.NA,
        })
    return pd.DataFrame(rows)
