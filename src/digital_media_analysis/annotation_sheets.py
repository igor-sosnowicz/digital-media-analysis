"""Write blind annotation workbooks and read the filled-in labels back.

One workbook per annotator holds an instruction sheet and one sheet per platform.
Instrument output is never included, so annotators code blind. Label columns use
the names from `annotation_columns` in the codebook. `cites_source` is not in
the sheet: reading derives it from `source_types` (codebook rule R13).
"""

import json
from pathlib import Path

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from digital_media_analysis.codebook import NO_SOURCE, Codebook
from digital_media_analysis.instruments.labels import LABEL_SEPARATOR

SHEET_NAMES = {"reddit": "Reddit", "wikipedia": "Wikipedia"}
# (unit column, header, width) for the read-only part of each sheet.
CONTENT_COLUMNS = {
    "reddit": [("unit_id", "unit_id", 12), ("group", "subreddit", 16), ("title", "tytuł", 40), ("text", "treść", 90), ("link", "link", 30)],
    "wikipedia": [("unit_id", "unit_id", 28), ("group", "strona", 22), ("text", "opis zmiany", 90)],
}
LABEL_COLUMNS = {
    "reddit": ["source_types", "uncertain", "notes", "annotator"],
    "wikipedia": ["source_types", "edit_about_sources", "uncertain", "notes", "annotator"],
}
BINARY_COLUMNS = ["edit_about_sources", "uncertain"]
LABEL_FILE_COLUMNS = [
    "unit_id", "platform", "annotator", "codebook_version",
    "cites_source", "source_types", "edit_about_sources", "uncertain", "notes",
]
EXCEL_CELL_LIMIT = 32_000
HEADER_FONT = Font(bold=True)
LABEL_FILL = PatternFill("solid", fgColor="FFF2CC")


def write_workbook(
    path: Path,
    annotator: str,
    phase: str,
    units_by_platform: dict[str, pd.DataFrame],
    codebook: Codebook,
) -> None:
    """Write one annotator's workbook; units must already be in presentation order."""
    workbook = Workbook()
    workbook.properties.title = f"{phase}_{annotator}"
    workbook.properties.description = json.dumps(
        {"phase": phase, "annotator": annotator, "codebook_version": codebook.version}
    )
    _write_instructions(workbook.active, annotator, phase, codebook)
    for platform, units in units_by_platform.items():
        _write_platform_sheet(workbook.create_sheet(SHEET_NAMES[platform]), platform, units, annotator, codebook)
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)


def _write_instructions(sheet, annotator: str, phase: str, codebook: Codebook) -> None:
    sheet.title = "Instrukcja"
    rows = [
        [f"Arkusz annotacji: {phase}, annotator {annotator}"],
        [f"Codebook v{codebook.version} z {codebook.date.isoformat()}. Pełna instrukcja: codebook/codebook.md"],
        [],
        ["Zasady pracy"],
        ["1. Koduj samodzielnie. Nie porównuj etykiet z innymi przed zakończeniem całego arkusza."],
        ["2. Opieraj się tylko na codebooku i tekście w wierszu. Nie otwieraj linków."],
        ["3. Wypełnij żółte kolumny w każdym wierszu. Zmienne binarne: 0 lub 1 (lista rozwijana)."],
        [f"4. source_types: kody z tabeli poniżej rozdzielone znakiem „{LABEL_SEPARATOR}”; {NO_SOURCE}, gdy nie ma powołania (sam, bez innych kodów; R13)."],
        ["5. W razie wątpliwości wybierz najlepszą etykietę, ustaw uncertain = 1 i opisz problem w notes (R12)."],
        ["6. Nie zmieniaj kolumn unit_id ani kolejności wierszy."],
        [],
        ["Kod", "Kategoria", "Definicja"],
        *([category.code, category.name, category.definition] for category in codebook.categories),
        [],
        ["Kolumna", "Opis"],
        *([column.name, column.description] for column in codebook.annotation_columns),
    ]
    for row in rows:
        sheet.append(row)
    for row in sheet.iter_rows():
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            if cell.column == 1 and cell.value in {"Zasady pracy", "Kod", "Kolumna"}:
                for header_cell in row:
                    header_cell.font = HEADER_FONT
    sheet["A1"].font = Font(bold=True, size=14)
    sheet.column_dimensions["A"].width = 22
    sheet.column_dimensions["B"].width = 45
    sheet.column_dimensions["C"].width = 90


def _write_platform_sheet(sheet, platform: str, units: pd.DataFrame, annotator: str, codebook: Codebook) -> None:
    content = CONTENT_COLUMNS[platform]
    labels = LABEL_COLUMNS[platform]
    sheet.append([header for _, header, _ in content] + labels)
    for unit in units.itertuples(index=False):
        values = [str(getattr(unit, column))[:EXCEL_CELL_LIMIT] for column, _, _ in content]
        sheet.append(values + [None] * (len(labels) - 1) + [annotator])

    last_row = len(units) + 1
    for index, (_, _, width) in enumerate(content, start=1):
        sheet.column_dimensions[get_column_letter(index)].width = width
    for offset, name in enumerate(labels, start=len(content) + 1):
        letter = get_column_letter(offset)
        sheet.column_dimensions[letter].width = 30 if name in {"source_types", "notes"} else 14
        for row in range(2, last_row + 1):
            sheet.cell(row, offset).fill = LABEL_FILL
        cell_range = f"{letter}2:{letter}{max(last_row, 2)}"
        if name in BINARY_COLUMNS:
            validation = DataValidation(type="list", formula1='"0,1"', allow_blank=True, showErrorMessage=True)
        elif name == "source_types":
            validation = DataValidation(allow_blank=True, showInputMessage=True)
            validation.promptTitle = "Kody kategorii"
            validation.prompt = LABEL_SEPARATOR.join(codebook.category_codes)
        else:
            continue
        sheet.add_data_validation(validation)
        validation.add(cell_range)

    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    for cell in sheet[1]:
        cell.font = HEADER_FONT
    sheet.freeze_panes = "B2"
    sheet.auto_filter.ref = f"A1:{get_column_letter(len(content) + len(labels))}{last_row}"


def read_workbook(path: Path, codebook: Codebook) -> tuple[pd.DataFrame, list[str]]:
    """Return the labels of a filled workbook and a list of problems found.

    Rows with problems are still returned, with the offending value set to missing,
    so the problems can be fixed in the workbook and the file read again.
    """
    workbook = load_workbook(path, read_only=True, data_only=True)
    metadata = _metadata(workbook)
    known_codes = set(codebook.category_codes)
    labeled, problems = [], []
    for platform, sheet_name in SHEET_NAMES.items():
        if sheet_name not in workbook.sheetnames:
            continue
        rows = list(workbook[sheet_name].iter_rows(values_only=True))
        header, body = list(rows[0]), rows[1:]
        expected = [name for _, name, _ in CONTENT_COLUMNS[platform]] + LABEL_COLUMNS[platform]
        if header[: len(expected)] != expected:
            problems.append(f"{sheet_name}: nagłówki {header} różnią się od oczekiwanych {expected}.")
            continue
        for excel_row, values in enumerate(body, start=2):
            record = dict(zip(header, values))
            if record["unit_id"] is None:
                continue
            where = f"{sheet_name}, wiersz {excel_row} ({record['unit_id']})"
            label = {
                "unit_id": str(record["unit_id"]),
                "platform": platform,
                "annotator": record["annotator"],
                "codebook_version": metadata.get("codebook_version", ""),
            }
            for name in BINARY_COLUMNS:
                if name not in record:
                    label[name] = pd.NA
                    continue
                value, problem = _binary(record[name], required=name != "uncertain")
                label[name] = value
                if problem:
                    problems.append(f"{where}: {name} {problem}")
            label["uncertain"] = 0 if pd.isna(label["uncertain"]) else label["uncertain"]

            raw_codes = str(record["source_types"] or "").replace(",", LABEL_SEPARATOR)
            codes = [code.strip().lower() for code in raw_codes.split(LABEL_SEPARATOR)]
            codes = sorted({code for code in codes if code})
            if unknown := [code for code in codes if code not in known_codes]:
                problems.append(f"{where}: nieznane kody {unknown}")
                codes = [code for code in codes if code in known_codes]
            label["source_types"] = LABEL_SEPARATOR.join(codes)
            # cites_source follows from source_types (R13); missing when the label is unusable.
            if not codes:
                if not unknown:
                    problems.append(f"{where}: source_types brak wartości (wpisz {NO_SOURCE}, gdy nie ma powołania)")
                label["cites_source"] = pd.NA
            elif NO_SOURCE in codes and len(codes) > 1:
                problems.append(f"{where}: {NO_SOURCE} razem z innymi kodami ({label['source_types']})")
                label["cites_source"] = pd.NA
            else:
                label["cites_source"] = int(codes != [NO_SOURCE])
            label["notes"] = "" if record["notes"] is None else str(record["notes"])
            labeled.append(label)
    return pd.DataFrame(labeled, columns=LABEL_FILE_COLUMNS), problems


def _metadata(workbook) -> dict:
    """Phase, annotator and codebook version stored by `write_workbook` ({} if absent)."""
    try:
        return json.loads(workbook.properties.description or "{}")
    except json.JSONDecodeError:
        return {}


def _binary(value, required: bool) -> tuple[object, str]:
    """Parse a 0/1 cell; return (value or NA, problem description or '')."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return pd.NA, "brak wartości" if required else ""
    try:
        number = float(str(value).strip().replace(",", "."))
    except ValueError:
        return pd.NA, f"ma wartość {value!r} zamiast 0 lub 1"
    if number not in (0, 1):
        return pd.NA, f"ma wartość {value!r} zamiast 0 lub 1"
    return int(number), ""
