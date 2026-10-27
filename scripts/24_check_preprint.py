"""Check the preprint before submission and build the Overleaf package (docs/plan_dokonczenia.md, Stage 7).

Reports every result macro used in report/preprint.tex but not defined in
report/numbers.tex, macros used in the text or tables whose value is still a
placeholder ([czeka na H1-A], [czeka na dane]), boxes \\dopisania{} not yet
replaced by text, and tables or figures the preprint needs but that do not
exist. With `--strict` it exits with an error while anything is left (before
submission); `--zip` writes the Overleaf package with preprint.tex,
numbers.tex and only the tables and figures the preprint uses.
"""

import argparse
import re
import sys
import zipfile
from pathlib import Path

from digital_media_analysis.paths import PROJECT_ROOT

REPORT_DIR = PROJECT_ROOT / "report"
PLACEHOLDERS = {r"\resPending", r"\resWaiting"}


def macro_values(numbers_text: str) -> dict[str, str]:
    """Macro name (without backslash) -> its definition, from numbers.tex."""
    return dict(re.findall(r"^\\newcommand\{\\(res[A-Za-z]+)\}\{(.*)\}$", numbers_text, flags=re.MULTILINE))


def check(report_dir: Path = REPORT_DIR) -> tuple[list[str], list[Path]]:
    """Problems found, and the files the preprint needs (preprint.tex, numbers.tex, tables, figures)."""
    preprint = (report_dir / "preprint.tex").read_text(encoding="utf-8")
    values = macro_values((report_dir / "numbers.tex").read_text(encoding="utf-8"))
    body = "\n".join(line for line in preprint.splitlines() if not line.lstrip().startswith("%"))
    tables = re.findall(r"\\(?:tabela|szeroka)\{([^}]+)\}", body)
    figures = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", body)
    needed = [report_dir / "preprint.tex", report_dir / "numbers.tex",
              *(report_dir / "tables" / f"{name}.tex" for name in tables),
              *(report_dir / "figures" / name for name in figures)]
    problems = [f"brak pliku {path.relative_to(report_dir)}" for path in needed if not path.exists()]

    used = set(re.findall(r"\\(res[A-Z][A-Za-z]*)", preprint))
    problems += [f"makro \\{name} nie jest zdefiniowane w numbers.tex" for name in sorted(used - set(values))]
    texts = [body, *(path.read_text(encoding="utf-8") for path in needed[2:2 + len(tables)] if path.exists())]
    shown = {name for text in texts for name in re.findall(r"\\(res[A-Z][A-Za-z]*)", text)}
    waiting = sorted(name for name in shown if name in values and values[name].strip() in PLACEHOLDERS)
    if waiting:
        problems.append(f"{len(waiting)} makr w tekście lub tabelach ma jeszcze wartość zastępczą, np. "
                        + ", ".join(f"\\{name}" for name in waiting[:6]))
    raw = sum(text.count(placeholder) for text in texts[1:] for placeholder in PLACEHOLDERS)
    if raw:
        problems.append(f"tabele zawierają {raw} wartości zastępczych")
    boxes = len(re.findall(r"^\\dopisania\{", body, flags=re.MULTILINE))
    if boxes:
        problems.append(f"{boxes} ramek \\dopisania{{}} do zastąpienia tekstem")
    return problems, needed


def build_zip(needed: list[Path], path: Path, report_dir: Path = REPORT_DIR) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for file in needed:
            if file.exists():
                archive.write(file, file.relative_to(report_dir).as_posix())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="Exit with an error while anything is left.")
    parser.add_argument("--zip", type=Path, help="Write the Overleaf package to this path, e.g. data/preprint_overleaf.zip.")
    args = parser.parse_args()
    problems, needed = check()
    for problem in problems:
        print(f"- {problem}")
    print("Preprint gotowy do oddania." if not problems else f"{len(problems)} rzeczy do dokończenia.")
    if args.zip:
        build_zip(needed, args.zip)
        print(f"Paczka Overleaf: {args.zip} ({sum(file.exists() for file in needed)} plików)")
    if problems and args.strict:
        sys.exit(1)


if __name__ == "__main__":
    main()
