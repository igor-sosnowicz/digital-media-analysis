import pandas as pd
from openpyxl import load_workbook

from digital_media_analysis.annotation_sheets import read_workbook, write_workbook
from digital_media_analysis.codebook import load_codebook


def units() -> dict[str, pd.DataFrame]:
    return {
        "reddit": pd.DataFrame({
            "unit_id": ["r1", "r2"],
            "group": "lodz",
            "title": ["Tytuł", "Inny"],
            "text": ["Według GUS…", ""],
            "link": ["", "https://wiadomosci.wp.pl/x"],
        }),
        "wikipedia": pd.DataFrame({
            "unit_id": ["COVID-19#3", "COVID-19#4"],
            "group": "COVID-19",
            "text": ["[[WP:SK]]", "wg WHO"],
        }),
    }


def fill(path, values: dict[str, list[list]]) -> None:
    workbook = load_workbook(path)
    for sheet_name, rows in values.items():
        sheet = workbook[sheet_name]
        header = [cell.value for cell in sheet[1]]
        for row_number, row_values in enumerate(rows, start=2):
            for name, value in zip(["cites_source", "source_types", "edit_about_sources", "uncertain", "notes"], row_values):
                if name in header:
                    sheet.cell(row_number, header.index(name) + 1, value)
    workbook.save(path)


def test_workbook_is_blind_and_prefilled(tmp_path):
    path = tmp_path / "pilot_A.xlsx"
    write_workbook(path, "A", "pilot", units(), load_codebook())
    workbook = load_workbook(path)
    assert workbook.sheetnames == ["Instrukcja", "Reddit", "Wikipedia"]
    header = [cell.value for cell in workbook["Wikipedia"][1]]
    assert header == ["unit_id", "strona", "opis zmiany", "cites_source", "source_types",
                      "edit_about_sources", "uncertain", "notes", "annotator"]
    assert "edit_about_sources" not in [cell.value for cell in workbook["Reddit"][1]]
    reddit_header = [cell.value for cell in workbook["Reddit"][1]]
    assert workbook["Reddit"].cell(2, reddit_header.index("annotator") + 1).value == "A"


def test_round_trip_returns_clean_labels(tmp_path):
    path = tmp_path / "pilot_A.xlsx"
    write_workbook(path, "A", "pilot", units(), load_codebook())
    fill(path, {
        "Reddit": [[1, "Oficjalne; media", None, None, None], [0, None, None, 1, "R2?"]],
        "Wikipedia": [["0", None, 0, None, None], [1, "oficjalne", "0", None, None]],
    })
    labels, problems = read_workbook(path, load_codebook())
    assert problems == []
    assert labels[["unit_id", "cites_source", "source_types", "uncertain"]].values.tolist() == [
        ["r1", 1, "media;oficjalne", 0],
        ["r2", 0, "", 1],
        ["COVID-19#3", 0, "", 0],
        ["COVID-19#4", 1, "oficjalne", 0],
    ]
    assert labels["annotator"].eq("A").all()


def test_problems_are_reported(tmp_path):
    path = tmp_path / "pilot_B.xlsx"
    write_workbook(path, "B", "pilot", units(), load_codebook())
    fill(path, {
        "Reddit": [[1, "medai", None, None, None], [2, None, None, None, None]],
        "Wikipedia": [[0, "media", None, None, None], [None, None, 1, None, None]],
    })
    _, problems = read_workbook(path, load_codebook())
    assert any("r1" in problem and "nieznane kody ['medai']" in problem for problem in problems)
    assert any("r1" in problem and "source_types jest puste" in problem for problem in problems)
    assert any("r2" in problem and "zamiast 0 lub 1" in problem for problem in problems)
    assert any("COVID-19#3" in problem and "cites_source = 0, ale" in problem for problem in problems)
    assert any("COVID-19#3" in problem and "edit_about_sources brak wartości" in problem for problem in problems)
    assert any("COVID-19#4" in problem and "cites_source brak wartości" in problem for problem in problems)
