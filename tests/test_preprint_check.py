import importlib.util
import zipfile

from digital_media_analysis.paths import PROJECT_ROOT


def load_script():
    spec = importlib.util.spec_from_file_location("check_preprint", PROJECT_ROOT / "scripts" / "24_check_preprint.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_report(folder, number: str, box: bool) -> None:
    (folder / "tables").mkdir(parents=True)
    (folder / "figures").mkdir()
    (folder / "figures" / "a.png").write_bytes(b"png")
    (folder / "tables" / "t.tex").write_text("x & \\resResult \\\\\n", encoding="utf-8")
    (folder / "numbers.tex").write_text("\\newcommand{\\resResult}{" + number + "}\n", encoding="utf-8")
    text = [r"\input{numbers}", r"Wynik \resResult.", r"% \resUnknownInComment", r"\tabela{t}",
            r"\includegraphics[width=1cm]{a.png}"]
    if box:
        text.append(r"\dopisania{wstęp}")
    (folder / "preprint.tex").write_text("\n".join(text) + "\n", encoding="utf-8")


def test_check_reports_placeholders_boxes_and_undefined_macros(tmp_path):
    script = load_script()
    write_report(tmp_path, r"\resWaiting", box=True)
    problems, needed = script.check(tmp_path)
    assert any("wartość zastępczą" in problem for problem in problems)
    assert any(r"\dopisania" in problem for problem in problems)
    assert any("resUnknownInComment" in problem for problem in problems)
    script.build_zip(needed, tmp_path / "out.zip", tmp_path)
    assert sorted(zipfile.ZipFile(tmp_path / "out.zip").namelist()) == ["figures/a.png", "numbers.tex", "preprint.tex", "tables/t.tex"]


def test_check_passes_a_finished_preprint(tmp_path):
    script = load_script()
    write_report(tmp_path / "r", "0{,}5", box=False)
    (tmp_path / "r" / "preprint.tex").write_text("\\input{numbers}\nWynik \\resResult.\n\\tabela{t}\n", encoding="utf-8")
    problems, _ = script.check(tmp_path / "r")
    assert problems == []


def test_check_counts_point_boxes(tmp_path):
    script = load_script()
    write_report(tmp_path, "1", box=False)
    with (tmp_path / "preprint.tex").open("a", encoding="utf-8") as handle:
        handle.write("\punkty{wstęp}{\item fakt}\n")
    problems, _ = script.check(tmp_path)
    assert any(r"\punkty" in problem for problem in problems)
