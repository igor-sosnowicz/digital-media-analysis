"""Import filled annotation workbooks into text-free label files and load them back.

Workbooks live in `annotations/sheets/<phase>_<annotator>.xlsx` (outside git, they
contain post text). Labels go to `annotations/labels/<phase>/<annotator>.csv`
(tracked), with unit IDs and labels only.
"""

from pathlib import Path

import pandas as pd

from digital_media_analysis.annotation_sheets import LABEL_FILE_COLUMNS, read_workbook
from digital_media_analysis.codebook import Codebook
from digital_media_analysis.gold import PHASE_SPLITS
from digital_media_analysis.paths import LABELS_DIR, SHEETS_DIR


def workbook_paths(phase: str, sheets_dir: Path = SHEETS_DIR) -> dict[str, Path]:
    """Map annotator ID to the workbook path for files named `<phase>_<annotator>.xlsx`."""
    prefix = f"{phase}_"
    return {path.stem.removeprefix(prefix): path for path in sorted(sheets_dir.glob(f"{prefix}*.xlsx"))}


def check_against_manifest(
    labels: pd.DataFrame, manifest: pd.DataFrame, phase: str, annotator: str
) -> list[str]:
    """Problems with the set of units in a workbook: missing, unexpected or repeated rows."""
    problems = []
    expected = manifest[manifest["split"].isin(PHASE_SPLITS[phase])]
    for platform, rows in expected.groupby("platform"):
        coded = labels.loc[labels["platform"].eq(platform), "unit_id"]
        if repeated := sorted(coded[coded.duplicated()].unique()):
            problems.append(f"{platform}: powtórzone unit_id {repeated}")
        if missing := sorted(set(rows["unit_id"]) - set(coded)):
            problems.append(f"{platform}: brak {len(missing)} jednostek z manifestu, np. {missing[:3]}")
        if unexpected := sorted(set(coded) - set(rows["unit_id"])):
            problems.append(f"{platform}: {len(unexpected)} jednostek spoza fazy {phase!r}, np. {unexpected[:3]}")
    if mismatched := sorted(set(labels["annotator"].astype(str)) - {annotator}):
        problems.append(f"kolumna annotator zawiera {mismatched}, a plik należy do {annotator!r}")
    return problems


def import_workbook(
    path: Path, annotator: str, phase: str, manifest: pd.DataFrame, codebook: Codebook
) -> tuple[pd.DataFrame, list[str]]:
    """Read one filled workbook; return its labels and every problem found."""
    labels, problems = read_workbook(path, codebook)
    return labels, problems + check_against_manifest(labels, manifest, phase, annotator)


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
