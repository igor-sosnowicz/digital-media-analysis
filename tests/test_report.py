import numpy as np

from digital_media_analysis import report


def test_numbers_use_a_decimal_comma_and_a_typeset_minus():
    assert report.number(0.456) == "0{,}46"
    assert report.number(-0.031) == "$-$0{,}03"
    # A value that rounds to zero carries no minus sign.
    assert report.number(-0.001) == "0{,}00"
    assert report.number(np.nan) == "--"
    assert report.interval(0.1, 0.25) == "[0{,}10; 0{,}25]"
    assert report.interval(np.nan, 0.2) == ""
    assert report.p_value(0.0004) == "$<$0{,}001" and report.p_value(0.0283) == "0{,}028"


def test_special_characters_are_escaped():
    assert report.escape("50% of #1 & co_x") == r"50\% of \#1 \& co\_x"
    assert report.code("cites_source") == r"\texttt{cites\_source}"


def test_tabular_shows_a_repeated_first_column_once_and_separates_groups():
    text = report.tabular(["", "x"], [["Reddit", "1"], ["Reddit", "2"], ["Wikipedia", "3"]], "lr", groups=[2])
    lines = text.splitlines()
    assert lines[0] == r"\begin{tabular}{lr}" and lines[-1] == r"\end{tabular}"
    assert lines[4:8] == [r"Reddit & 1 \\", r" & 2 \\", r"\midrule", r"Wikipedia & 3 \\"]
