"""LaTeX fragments for the report (report/raport.tex): numbers in Polish notation and booktabs tables.

Tables are generated from the result files (`scripts/13_report_tables.py`), so
no number is copied by hand. Each fragment is a bare `tabular`; captions and
labels stay in the report text. Output is plain pdflatex input: no Unicode
math symbols, a decimal comma and `$-$` for a minus sign.
"""

from collections.abc import Sequence

import numpy as np

SPECIAL = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
           "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}


def escape(text: object) -> str:
    """Text with the LaTeX special characters escaped."""
    return "".join(SPECIAL.get(character, character) for character in str(text))


def code(name: str) -> str:
    """A code name in typewriter type, e.g. `cites_source`."""
    return rf"\texttt{{{escape(name)}}}"


def number(value: float, digits: int = 2) -> str:
    """A number with a decimal comma and a typeset minus; a dash when missing."""
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "--"
    text = f"{abs(float(value)):.{digits}f}".replace(".", "{,}")
    return ("$-$" if float(value) < 0 and text.strip("0{,}") else "") + text


def interval(low: float, high: float, digits: int = 2) -> str:
    if low is None or high is None or not (np.isfinite(low) and np.isfinite(high)):
        return ""
    return f"[{number(low, digits)}; {number(high, digits)}]"


def estimate(value: float, low: float, high: float, digits: int = 2) -> str:
    """A value with its interval below it in a smaller font, for narrow columns."""
    bounds = interval(low, high, digits)
    return number(value, digits) + (rf" {{\scriptsize {bounds}}}" if bounds else "")


def p_value(value: float) -> str:
    if value is None or not np.isfinite(value):
        return "--"
    return "$<$0{,}001" if value < 0.001 else number(value, 3)


def tabular(header: Sequence[str], rows: Sequence[Sequence[str]], align: str, groups: Sequence[int] = ()) -> str:
    """A booktabs `tabular`; `groups` are the row indices before which a \\midrule separates groups.

    A first-column value repeated in consecutive rows is shown only once.
    """
    lines = [rf"\begin{{tabular}}{{{align}}}", r"\toprule", " & ".join(header) + r" \\", r"\midrule"]
    rows = [[*row] for row in rows]
    for index in range(len(rows) - 1, 0, -1):
        if rows[index][0] == rows[index - 1][0]:
            rows[index][0] = ""
    for index, row in enumerate(rows):
        if index in groups:
            lines.append(r"\midrule")
        lines.append(" & ".join(row) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", ""]
    return "\n".join(lines)
