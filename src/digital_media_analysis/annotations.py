"""Import filled annotation workbooks into text-free label files and load them back.

Workbooks live in `annotations/sheets/<phase>_<annotator>.xlsx` (outside git, they
contain post text). Labels go to `annotations/labels/<phase>/<annotator>.csv`
(tracked), with unit IDs and labels only.
"""

import re
from pathlib import Path

import pandas as pd

from digital_media_analysis.annotation_sheets import LABEL_FILE_COLUMNS, SHEET_NAMES, read_workbook
from digital_media_analysis.codebook import Codebook
from digital_media_analysis.gold import phase_mask
from digital_media_analysis.paths import LABELS_DIR, SHEETS_DIR


def workbook_paths(phase: str, sheets_dir: Path = SHEETS_DIR) -> dict[str, Path]:
    """Map annotator ID to the workbook path for files named `<phase>_<annotator>.xlsx`."""
    prefix = f"{phase}_"
    return {path.stem.removeprefix(prefix): path for path in sorted(sheets_dir.glob(f"{prefix}*.xlsx"))}


def check_against_manifest(
    labels: pd.DataFrame, manifest: pd.DataFrame, phase: str, annotator: str, partial: bool = False
) -> list[str]:
    """Problems with the set of units in a workbook: missing, unexpected or repeated rows.

    With `partial` (a phase split between annotators), missing units are expected.
    """
    problems = []
    expected = manifest[phase_mask(manifest, phase)]
    for platform, rows in expected.groupby("platform"):
        coded = labels.loc[labels["platform"].eq(platform), "unit_id"]
        if repeated := sorted(coded[coded.duplicated()].unique()):
            problems.append(f"{platform}: powtórzone unit_id {repeated}")
        if not partial and (missing := sorted(set(rows["unit_id"]) - set(coded))):
            problems.append(f"{platform}: brak {len(missing)} jednostek z manifestu, np. {missing[:3]}")
        if unexpected := sorted(set(coded) - set(rows["unit_id"])):
            problems.append(f"{platform}: {len(unexpected)} jednostek spoza fazy {phase!r}, np. {unexpected[:3]}")
    if mismatched := sorted(set(labels["annotator"].astype(str)) - {annotator}):
        problems.append(f"kolumna annotator zawiera {mismatched}, a plik należy do {annotator!r}")
    return problems


def import_workbook(
    path: Path, annotator: str, phase: str, manifest: pd.DataFrame, codebook: Codebook, partial: bool = False
) -> tuple[pd.DataFrame, list[str]]:
    """Read one filled workbook; return its labels and every problem found.

    With `partial`, rows without labels are skipped and missing units are not a
    problem, so a workbook coded only in part, or holding part of the phase, imports.
    """
    labels, problems = read_workbook(path, codebook, partial=partial)
    return labels, problems + check_against_manifest(labels, manifest, phase, annotator, partial=partial)


# A problem of one sheet row, as `read_workbook` reports it: "<sheet>, wiersz <n> (<unit_id>): ...".
ROW_PROBLEM = re.compile(r"^(?P<sheet>\w+), wiersz \d+ \((?P<unit_id>.+?)\): ")


def drop_invalid_rows(labels: pd.DataFrame, problems: list[str]) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Labels without the rows that have problems, the problems of those rows, and the blocking problems.

    A row problem drops only its row. Header and manifest problems concern the
    whole workbook, so they stay blocking.
    """
    platform_of = {sheet: platform for platform, sheet in SHEET_NAMES.items()}
    row_problems, blocking, bad_rows = [], [], set()
    for problem in problems:
        if (match := ROW_PROBLEM.match(problem)) and match["sheet"] in platform_of:
            row_problems.append(problem)
            bad_rows.add((platform_of[match["sheet"]], match["unit_id"]))
        else:
            blocking.append(problem)
    keep = [(platform, unit_id) not in bad_rows for platform, unit_id in zip(labels["platform"], labels["unit_id"])]
    return labels[keep].reset_index(drop=True), row_problems, blocking


def label_path(phase: str, annotator: str, labels_dir: Path = LABELS_DIR) -> Path:
    return labels_dir / phase / f"{annotator}.csv"


def save_labels(labels: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    labels[LABEL_FILE_COLUMNS].to_csv(path, index=False, encoding="utf-8")


def load_labels(phase: str, labels_dir: Path = LABELS_DIR) -> pd.DataFrame:
    """All annotators' labels for a phase in one long table (empty if none imported yet)."""
    paths = sorted((labels_dir / phase).glob("*.csv"))
    if not paths:
        return pd.DataFrame(columns=LABEL_FILE_COLUMNS)
    labels = pd.concat(
        [
            pd.read_csv(
                path,
                dtype={"unit_id": str, "annotator": str, "codebook_version": str, "source_types": str, "notes": str},
                keep_default_na=False,
                na_values={"cites_source": [""], "edit_about_sources": [""], "uncertain": [""]},
            )
            for path in paths
        ],
        ignore_index=True,
    )
    for column in ["cites_source", "edit_about_sources", "uncertain"]:
        labels[column] = labels[column].astype("Int64")
    return labels


def gold_reference(labels: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """One reference label per unit from the imported labels of a phase, and the units left out.

    A unit coded by one person keeps that label. A unit several people coded keeps
    it only when they agree on `source_types` and `edit_about_sources`; otherwise
    it waits for adjudication and is returned in the second table.
    """
    labels = labels[labels["cites_source"].notna()]
    columns = ["source_types", "edit_about_sources"]
    agreed = labels.assign(_edit=labels["edit_about_sources"].astype("string").fillna("")).groupby(
        ["platform", "unit_id"]
    ).filter(lambda rows: rows[["source_types", "_edit"]].drop_duplicates().shape[0] == 1)
    reference = agreed.drop(columns="_edit").drop_duplicates(["platform", "unit_id"]).reset_index(drop=True)
    conflicts = labels[~labels.set_index(["platform", "unit_id"]).index.isin(reference.set_index(["platform", "unit_id"]).index)]
    return reference, conflicts[["unit_id", "platform", "annotator", *columns]].reset_index(drop=True)

