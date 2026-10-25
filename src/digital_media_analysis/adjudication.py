"""Adjudication: an arbiter settles the units that annotators coded differently.

`annotations.gold_reference` keeps a unit coded by several people only when they
agree; the rest waits for an arbiter. The arbiter workbook
(`annotations/sheets/adjudication_<phase>.xlsx`, outside git) is an ordinary
annotation workbook holding the disputed units, with every annotator's labels
and notes to the right of the label columns: the arbiter is not blind and
writes the final label, which may differ from all of them. Decisions go
text-free to `annotations/adjudication/<phase>.csv`; `gold_reference` uses them
for the disputed units they cover.
"""

from pathlib import Path

import pandas as pd

from digital_media_analysis.annotation_sheets import LABEL_FILE_COLUMNS, read_workbook, write_workbook
from digital_media_analysis.annotations import gold_reference, read_label_file
from digital_media_analysis.codebook import Codebook
from digital_media_analysis.paths import ADJUDICATION_DIR, SHEETS_DIR

ARBITER_RULES = [
    ("To arkusz arbitra, nie jest ślepy: na prawo od żółtych kolumn są etykiety i notatki annotatorów. "
     "Wpisz etykietę ostateczną według codebooka; może różnić się od wszystkich."),
    "W notes zapisz krótko powód rozstrzygnięcia (np. numer reguły). Z tych powodów powstają poprawki codebooka.",
]
SHOWN = ["source_types", "edit_about_sources", "uncertain", "notes"]


def sheet_path(phase: str, sheets_dir: Path = SHEETS_DIR) -> Path:
    return sheets_dir / f"adjudication_{phase}.xlsx"


def decisions_path(phase: str, adjudication_dir: Path = ADJUDICATION_DIR) -> Path:
    return adjudication_dir / f"{phase}.csv"


def disputed(labels: pd.DataFrame) -> pd.DataFrame:
    """One row per disputed unit (platform, unit_id), with `<annotator>: <column>` for every annotator's label."""
    _, conflicts = gold_reference(labels)
    keys = conflicts[["platform", "unit_id"]].drop_duplicates()
    coded = labels.merge(keys, on=["platform", "unit_id"])
    rows = []
    for (platform, unit_id), group in coded.groupby(["platform", "unit_id"], sort=False):
        row = {"platform": platform, "unit_id": unit_id}
        for label in group.sort_values("annotator").itertuples(index=False):
            for column in SHOWN:
                if column == "edit_about_sources" and platform != "wikipedia":
                    continue
                value = getattr(label, column)
                row[f"{label.annotator}: {column}"] = "" if pd.isna(value) else str(value)
        rows.append(row)
    shown = [f"{annotator}: {column}" for annotator in sorted(coded["annotator"].unique()) for column in SHOWN]
    frame = pd.DataFrame(rows, columns=["platform", "unit_id", *shown])
    return frame.dropna(axis=1, how="all")


def write_sheet(
    path: Path, phase: str, arbiter: str, disputes: pd.DataFrame, units_by_platform: dict[str, pd.DataFrame], codebook: Codebook
) -> dict[str, int]:
    """Arbiter workbook with the disputed units in the order of `units_by_platform`; returns units per platform."""
    shown = {}
    for platform, units in units_by_platform.items():
        rows = disputes[disputes["platform"].eq(platform)].dropna(axis=1, how="all").drop(columns="platform")
        shown[platform] = units.merge(rows, on="unit_id")
    context = list(dict.fromkeys(
        column for frame in shown.values() for column in frame.columns if ": " in column
    ))
    for platform, frame in shown.items():
        shown[platform] = frame.reindex(columns=[*frame.columns.difference(context, sort=False), *context])
    write_workbook(path, arbiter, phase, shown, codebook, context_columns=context, extra_rules=ARBITER_RULES)
    return {platform: len(frame) for platform, frame in shown.items()}


def read_decisions(path: Path, codebook: Codebook, disputes: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """The arbiter's labels (rows left empty are undecided) and the problems found, as for an annotation workbook."""
    decisions, problems = read_workbook(path, codebook, partial=True)
    keys = set(zip(disputes["platform"], disputes["unit_id"].astype(str)))
    if extra := sorted(unit for platform, unit in zip(decisions["platform"], decisions["unit_id"]) if (platform, unit) not in keys):
        problems.append(f"{len(extra)} rozstrzygnięć dotyczy jednostek bez sporu, np. {extra[:3]}")
    return decisions, problems


def save_decisions(decisions: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    decisions[LABEL_FILE_COLUMNS].to_csv(path, index=False, encoding="utf-8")


def load_decisions(phase: str, adjudication_dir: Path = ADJUDICATION_DIR) -> pd.DataFrame:
    """The arbiter's decisions for a phase (empty when there are none yet)."""
    path = decisions_path(phase, adjudication_dir)
    return read_label_file(path) if path.exists() else pd.DataFrame(columns=LABEL_FILE_COLUMNS)
