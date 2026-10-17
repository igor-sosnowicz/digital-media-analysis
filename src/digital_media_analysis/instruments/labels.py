"""Convert mention-level instrument output into document labels in codebook space."""

from collections.abc import Collection, Mapping

import pandas as pd

LABEL_SEPARATOR = ";"


def to_document_labels(
    mentions: pd.DataFrame,
    units: pd.DataFrame,
    unit_columns: list[str],
    category_column: str,
    category_map: Mapping[str, str | None],
    non_citation: Collection[str] = (),
) -> pd.DataFrame:
    """Return one row per unit with `cites_source` (0/1) and `source_types`.

    `source_types` holds sorted codebook codes joined with `LABEL_SEPARATOR`,
    the same format as the annotation sheet. Units without mentions get
    `cites_source = 0` and an empty `source_types`.
    """
    unknown = set(mentions[category_column]) - set(category_map) - set(non_citation)
    if unknown:
        raise ValueError(f"Categories missing from the codebook mapping: {sorted(unknown)}")

    citing = mentions[~mentions[category_column].isin(non_citation)]
    codes = citing[category_column].map(category_map)
    source_types = (
        citing.assign(code=codes)
        .dropna(subset=["code"])
        .groupby(unit_columns)["code"]
        .agg(lambda values: LABEL_SEPARATOR.join(sorted(set(values))))
    )
    cited_units = citing.groupby(unit_columns).size().index

    labels = units[unit_columns].drop_duplicates().set_index(unit_columns)
    labels["cites_source"] = labels.index.isin(cited_units).astype(int)
    labels["source_types"] = source_types.reindex(labels.index).fillna("")
    return labels.reset_index()
