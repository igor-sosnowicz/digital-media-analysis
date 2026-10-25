"""Stance pass: blind workbooks for `consensus_stance` on Reddit posts, their import, reference and agreement.

The stance of a post toward the scientific consensus (codebook variable
`consensus_stance`, rule R14) is coded in a pass of its own, so the source
workbooks of codebook 2.0 stay as they are. A stance workbook,
`annotations/sheets/stance_<phase>_<annotator>.xlsx`, holds the Reddit posts and
the columns consensus_stance, uncertain, notes and annotator. Imported labels go
to `annotations/labels/<phase>/stance_<annotator>.csv`, without post text.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from digital_media_analysis.agreement import cohen_kappa, krippendorff_alpha
from digital_media_analysis.annotation_sheets import (
    CONTENT_COLUMNS,
    EXCEL_CELL_LIMIT,
    HEADER_FONT,
    LABEL_FILL,
    _binary,
    _metadata,
)
from digital_media_analysis.codebook import Codebook
from digital_media_analysis.paths import LABELS_DIR, SHEETS_DIR

STANCE = "consensus_stance"
SHEET_NAME = "Reddit"
LABEL_COLUMNS = [STANCE, "uncertain", "notes", "annotator"]
FILE_COLUMNS = ["unit_id", "platform", "annotator", "codebook_version", STANCE, "uncertain", "notes"]
# Values that say nothing about trust in science.
NOT_APPLICABLE = "not_applicable"


def stance_values(codebook: Codebook) -> list[str]:
    return list(codebook.variable(STANCE).values)


def workbook_path(phase: str, annotator: str, sheets_dir: Path = SHEETS_DIR) -> Path:
    return sheets_dir / f"stance_{phase}_{annotator}.xlsx"


def workbook_paths(phase: str, sheets_dir: Path = SHEETS_DIR) -> dict[str, Path]:
    """Annotator ID -> stance workbook of a phase."""
    prefix = f"stance_{phase}_"
    return {path.stem.removeprefix(prefix): path for path in sorted(sheets_dir.glob(f"{prefix}*.xlsx"))}


def label_path(phase: str, annotator: str, labels_dir: Path = LABELS_DIR) -> Path:
    return labels_dir / phase / f"stance_{annotator}.csv"


def write_workbook(path: Path, annotator: str, phase: str, units: pd.DataFrame, codebook: Codebook) -> None:
    """Write one annotator's stance workbook; `units` are Reddit units in presentation order."""
    variable = codebook.variable(STANCE)
    rule = next(rule.text for rule in codebook.rules if rule.code == "R14")
    workbook = Workbook()
    workbook.properties.title = f"stance_{phase}_{annotator}"
    workbook.properties.description = json.dumps(
        {"phase": phase, "annotator": annotator, "codebook_version": codebook.version, "pass": "stance"}
    )
    instructions = workbook.active
    instructions.title = "Instrukcja"
    rows = [
        [f"Arkusz stanowiska: {phase}, annotator {annotator}"],
        [f"Codebook v{codebook.version} z {codebook.date.isoformat()}. Pełna instrukcja: codebook/codebook.md i docs/instrukcja_annotacji_reddit.md"],
        [],
        ["Zasady pracy"],
        ["1. Koduj samodzielnie. Nie porównuj etykiet z innymi przed zakończeniem całego arkusza."],
        ["2. Opieraj się tylko na tytule, treści i adresie linku w wierszu. Nie otwieraj linków."],
        [f"3. {STANCE}: jedna wartość z tabeli poniżej (lista rozwijana)."],
        ["4. W razie wątpliwości wybierz najlepszą wartość, ustaw uncertain = 1 i opisz problem w notes (R12)."],
        ["5. Nie zmieniaj kolumn unit_id ani kolejności wierszy."],
        [],
        [variable.question],
        ["Wartość", "Znaczenie"],
        *([value, meaning] for value, meaning in variable.values.items()),
        [],
        ["R14", rule],
    ]
    for row in rows:
        instructions.append(row)
    for row in instructions.iter_rows():
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            if cell.column == 1 and cell.value in {"Zasady pracy", "Wartość"}:
                for header_cell in row:
                    header_cell.font = HEADER_FONT
    instructions["A1"].font = Font(bold=True, size=14)
    instructions.column_dimensions["A"].width = 22
    instructions.column_dimensions["B"].width = 110

    sheet = workbook.create_sheet(SHEET_NAME)
    content = CONTENT_COLUMNS["reddit"]
    sheet.append([header for _, header, _ in content] + LABEL_COLUMNS)
    for unit in units.itertuples(index=False):
        values = [str(getattr(unit, column))[:EXCEL_CELL_LIMIT] for column, _, _ in content]
        sheet.append(values + [None] * (len(LABEL_COLUMNS) - 1) + [annotator])
    last_row = max(len(units) + 1, 2)
    for index, (_, _, width) in enumerate(content, start=1):
        sheet.column_dimensions[get_column_letter(index)].width = width
    for offset, name in enumerate(LABEL_COLUMNS, start=len(content) + 1):
        letter = get_column_letter(offset)
        sheet.column_dimensions[letter].width = 30 if name == "notes" else 16
        for row in range(2, len(units) + 2):
            sheet.cell(row, offset).fill = LABEL_FILL
        if name == STANCE:
            validation = DataValidation(type="list", formula1=f'"{",".join(variable.values)}"', allow_blank=True, showErrorMessage=True)
        elif name == "uncertain":
            validation = DataValidation(type="list", formula1='"0,1"', allow_blank=True, showErrorMessage=True)
        else:
            continue
        sheet.add_data_validation(validation)
        validation.add(f"{letter}2:{letter}{last_row}")
    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    for cell in sheet[1]:
        cell.font = HEADER_FONT
    sheet.freeze_panes = "B2"
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)


def read_workbook(path: Path, codebook: Codebook, partial: bool = False) -> tuple[pd.DataFrame, list[str]]:
    """Stance labels of a filled workbook and every problem found; with `partial`, rows without labels are skipped."""
    allowed = set(stance_values(codebook))
    workbook = load_workbook(path, read_only=True, data_only=True)
    metadata = _metadata(workbook)
    if SHEET_NAME not in workbook.sheetnames:
        return pd.DataFrame(columns=FILE_COLUMNS), [f"{path.name}: brak zakładki {SHEET_NAME}"]
    rows = list(workbook[SHEET_NAME].iter_rows(values_only=True))
    header, body = list(rows[0]), rows[1:]
    expected = [name for _, name, _ in CONTENT_COLUMNS["reddit"]] + LABEL_COLUMNS
    if header[: len(expected)] != expected:
        return pd.DataFrame(columns=FILE_COLUMNS), [f"{SHEET_NAME}: nagłówki {header} różnią się od oczekiwanych {expected}."]
    labels, problems = [], []
    for excel_row, values in enumerate(body, start=2):
        record = dict(zip(header, values))
        if record["unit_id"] is None:
            continue
        filled = any(record[name] not in (None, "") for name in (STANCE, "uncertain", "notes"))
        if partial and not filled:
            continue
        where = f"{SHEET_NAME}, wiersz {excel_row} ({record['unit_id']})"
        stance = str(record[STANCE] or "").strip().lower()
        if not stance:
            problems.append(f"{where}: {STANCE} brak wartości")
            stance = None
        elif stance not in allowed:
            problems.append(f"{where}: {STANCE} ma wartość {stance!r} spoza {sorted(allowed)}")
            stance = None
        uncertain, problem = _binary(record["uncertain"], required=False)
        if problem:
            problems.append(f"{where}: uncertain {problem}")
        labels.append({
            "unit_id": str(record["unit_id"]),
            "platform": "reddit",
            "annotator": record["annotator"],
            "codebook_version": metadata.get("codebook_version", ""),
            STANCE: stance,
            "uncertain": 0 if pd.isna(uncertain) else uncertain,
            "notes": "" if record["notes"] is None else str(record["notes"]),
        })
    return pd.DataFrame(labels, columns=FILE_COLUMNS), problems


def save_labels(labels: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    labels[FILE_COLUMNS].to_csv(path, index=False, encoding="utf-8")


def load_labels(phase: str, labels_dir: Path = LABELS_DIR) -> pd.DataFrame:
    """All annotators' stance labels of a phase (empty if none imported yet)."""
    paths = sorted((labels_dir / phase).glob("stance_*.csv"))
    if not paths:
        return pd.DataFrame(columns=FILE_COLUMNS)
    labels = pd.concat(
        [pd.read_csv(path, dtype={"unit_id": str, "annotator": str, "codebook_version": str, STANCE: str, "notes": str},
                     keep_default_na=False, na_values={STANCE: [""]}) for path in paths],
        ignore_index=True,
    )
    return labels.astype({"uncertain": "Int64"})


def reference(labels: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """One stance per unit: kept when everyone who coded the unit agrees; the rest waits for adjudication."""
    labels = labels[labels[STANCE].notna()]
    values_per_unit = labels.groupby("unit_id")[STANCE].nunique()
    agreed = values_per_unit[values_per_unit.eq(1)].index
    kept = labels[labels["unit_id"].isin(agreed)].drop_duplicates("unit_id").reset_index(drop=True)
    return kept, labels[~labels["unit_id"].isin(agreed)].reset_index(drop=True)


def agreement(labels: pd.DataFrame, samples: int = 2000, seed: int = 20261024) -> pd.DataFrame:
    """Agreement on units coded by two or more people: observed share, Cohen's kappa (two people) and Krippendorff's alpha."""
    labels = labels[labels[STANCE].notna()]
    matrix = labels.pivot_table(index="unit_id", columns="annotator", values=STANCE, aggfunc="first")
    rows = []
    for variable, transform in [(STANCE, lambda value: value), ("trust_relevant", lambda value: value != NOT_APPLICABLE)]:
        coded = matrix.map(lambda value: None if pd.isna(value) else transform(value))
        # Missing labels come back as NaN from DataFrame.map, so test with pd.isna, not `is None`.
        units = [[value for value in row if not pd.isna(value)] for row in coded.itertuples(index=False)]
        units = [row for row in units if len(row) >= 2]
        kappa = (
            cohen_kappa(coded.iloc[:, 0].tolist(), coded.iloc[:, 1].tolist(), samples, seed)
            if coded.shape[1] == 2 else None
        )
        alpha = krippendorff_alpha(units, samples=samples, seed=seed)
        rows.append({
            "variable": variable,
            "units": len(units),
            "annotators": coded.shape[1],
            "observed_agreement": float(np.mean([len(set(row)) == 1 for row in units])) if units else np.nan,
            "kappa": kappa.value if kappa else np.nan,
            "kappa_low": kappa.low if kappa else np.nan,
            "kappa_high": kappa.high if kappa else np.nan,
            "alpha": alpha.value,
            "alpha_low": alpha.low,
            "alpha_high": alpha.high,
        })
    return pd.DataFrame(rows)
