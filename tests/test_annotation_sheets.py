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
            for name, value in zip(["source_types", "edit_about_sources", "uncertain", "notes"], row_values):
                if name in header:
                    sheet.cell(row_number, header.index(name) + 1, value)
    workbook.save(path)


def test_workbook_is_blind_and_prefilled(tmp_path):
    path = tmp_path / "pilot_A.xlsx"
    write_workbook(path, "A", "pilot", units(), load_codebook())
    workbook = load_workbook(path)
    assert workbook.sheetnames == ["Instrukcja", "Reddit", "Wikipedia"]
    header = [cell.value for cell in workbook["Wikipedia"][1]]
    # cites_source is derived from source_types, so annotators do not fill it in.
    assert header == ["unit_id", "strona", "opis zmiany", "source_types",
                      "edit_about_sources", "uncertain", "notes", "annotator"]
    assert "edit_about_sources" not in [cell.value for cell in workbook["Reddit"][1]]
    reddit_header = [cell.value for cell in workbook["Reddit"][1]]
    assert workbook["Reddit"].cell(2, reddit_header.index("annotator") + 1).value == "A"


def test_round_trip_returns_clean_labels_and_derives_cites_source(tmp_path):
    path = tmp_path / "pilot_A.xlsx"
    write_workbook(path, "A", "pilot", units(), load_codebook())
    fill(path, {
        "Reddit": [["Institutional; media", None, None], ["none", None, 1, "R2?"]],
        "Wikipedia": [["None", 0, None], ["institutional", "0", None]],
    })
    labels, problems = read_workbook(path, load_codebook())
    assert problems == []
    assert labels[["unit_id", "cites_source", "source_types", "uncertain"]].values.tolist() == [
        ["r1", 1, "institutional;media", 0],
        ["r2", 0, "none", 1],
        ["COVID-19#3", 0, "none", 0],
        ["COVID-19#4", 1, "institutional", 0],
    ]
    assert labels["annotator"].eq("A").all()


def test_problems_are_reported(tmp_path):
    path = tmp_path / "pilot_B.xlsx"
    write_workbook(path, "B", "pilot", units(), load_codebook())
    fill(path, {
        "Reddit": [["medai", None, None], [None, None, 2]],
        "Wikipedia": [["none;media", None, None], ["oficjalne", 1, None]],
    })
    labels, problems = read_workbook(path, load_codebook())
    assert any("r1" in problem and "nieznane kody ['medai']" in problem for problem in problems)
    assert any("r2" in problem and "source_types brak wartości" in problem for problem in problems)
    assert any("r2" in problem and "uncertain ma wartość 2" in problem for problem in problems)
    assert any("COVID-19#3" in problem and "none razem z innymi kodami" in problem for problem in problems)
    assert any("COVID-19#3" in problem and "edit_about_sources brak wartości" in problem for problem in problems)
    # Polish v1.0 codes are no longer valid.
    assert any("COVID-19#4" in problem and "nieznane kody ['oficjalne']" in problem for problem in problems)
    # Empty `source_types` gives no cites_source (missing label).
    assert labels["cites_source"].isna().all()
