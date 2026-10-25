"""Tables and figures of the LaTeX report (report/raport.tex) from the saved result files.

Writes bare `tabular` fragments to report/tables/ and figures to report/figures/
(the pilot agreement and Pareto charts are copied, the yearly shares of the
hypotheses are drawn here), so report/ compiles on its own, e.g. on Overleaf.
Run it after the analyses whose results the report shows; it computes nothing new.
"""

import json
import shutil

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from digital_media_analysis import adjudication, annotations, gold  # noqa: E402
from digital_media_analysis.agreement import GRID, INK, INK_SECONDARY, SERIES, SURFACE  # noqa: E402
from digital_media_analysis.codebook import load_codebook  # noqa: E402
from digital_media_analysis.paths import (  # noqa: E402
    AGREEMENT_DIR,
    ERRORS_DIR,
    HYPOTHESES_DIR,
    PROJECT_ROOT,
    VALIDATION_DIR,
)
from digital_media_analysis.report import code, escape, estimate, interval, number, p_value, tabular  # noqa: E402

REPORT_DIR = PROJECT_ROOT / "report"
TABLES_DIR = REPORT_DIR / "tables"
FIGURES_DIR = REPORT_DIR / "figures"
INSTRUMENTS = {"rules_v1": "v1", "zeroshot_v1": "zero-shot", "gliner_v1": "GLiNER", "rules_v2": "reguły v2", "refs_v1": "I4"}
PLATFORMS = {"reddit": "Reddit", "wikipedia": "Wikipedia"}
H1_ANALYSES = {"primary": "główna (2005--2018)", "sensitivity_period": "2005--2020",
               "only_science": "tylko r/science", "only_conspiracy": "tylko r/conspiracy"}
H1_OUTCOMES = {"consensus": "źródła konsensusu (spadek)", "alternative": "źródła alternatywne (wzrost)"}
H2_ANALYSES = {"primary": "główna", "without_covid19": "bez strony COVID-19", "without_2020": "bez roku 2020",
               "classified_only": "tylko domeny sklasyfikowane"}
ROBUSTNESS = {
    "preregistered model (for comparison)": "model z preregistracji (dla porównania)",
    "Firth, all pages": "Firth, wszystkie strony",
    "Firth, pooled": "Firth, bez efektów stałych",
    "Firth, without 2026": "Firth, bez 2026 (rok niepełny)",
    "Firth, without 2020": "Firth, bez 2020",
    "Firth, without COVID-19": "Firth, bez strony COVID-19",
    "revision level, any alternative link": "poziom rewizji: czy dodała link alternatywny",
    "revision level, alternative links per revision": "poziom rewizji: liczba linków (Poisson)",
    "definition: social media and video only": "tylko media społecznościowe i wideo",
    "definition: broad (social_blog, other, unclassified)": "szeroka definicja (z \\texttt{other} i niesklasyfikowanymi)",
    "definition: established sources fall": "źródła ustalone maleją",
    "measurement: first addition of each link only": "tylko pierwsze dodanie linku",
    "measurement: owner of the post (WHO, GIS posts are institutional)": "właściciel posta (WHO, GIS jako instytucje)",
    "measurement: owner of the post, first additions only": "właściciel posta, tylko pierwsze dodania",
    "influence: preregistered model without one alternative link": "bez jednego linku alternatywnego (OR: mediana i zakres; największe $p$)",
}


def write(name: str, text: str) -> None:
    (TABLES_DIR / f"{name}.tex").write_text(text, encoding="utf-8")


def metric(table: pd.DataFrame, instrument: str, platform: str, variable: str, name: str, subset: str = "all") -> pd.Series | None:
    rows = table[(table["instrument"] == instrument) & (table["platform"] == platform) & (table["subset"] == subset)
                 & (table["variable"] == variable) & (table["metric"] == name)]
    return rows.iloc[0] if len(rows) else None


def metric_table(path) -> str:
    table = pd.read_csv(path)
    instruments = [name for name in INSTRUMENTS if name in set(table["instrument"])]
    specs = [
        ("reddit", "cites_source", "f1", "F1 " + code("cites_source")),
        ("reddit", "cites_source", "kappa", r"$\kappa$ " + code("cites_source")),
        ("reddit", "source_types", "masi", "MASI"),
        ("reddit", "source_types", "macro_f1", "macro-F1"),
        ("wikipedia", "cites_source", "f1", "F1 " + code("cites_source")),
        ("wikipedia", "edit_about_sources", "f1", "F1 " + code("edit_about_sources")),
        ("wikipedia", "source_types", "masi", "MASI"),
    ]
    rows = []
    for platform, variable, name, label in specs:
        cells = []
        for instrument in instruments:
            row = metric(table, instrument, platform, variable, name)
            interval_shown = name != "kappa"
            cells.append("--" if row is None else
                         estimate(row["value"], row["low"] if interval_shown else np.nan, row["high"] if interval_shown else np.nan))
        rows.append([PLATFORMS[platform], label, *cells])
    header = ["", "Miara", *(INSTRUMENTS[name] for name in instruments)]
    return tabular(header, rows, "ll" + "c" * len(instruments), groups=[4])


def sample_table() -> str:
    manifest = gold.load_manifest()
    reference, _ = annotations.gold_reference(annotations.load_labels("gold"), adjudication.load_decisions("gold"))
    coded = reference.merge(manifest[["unit_id", "platform", "split"]], on=["unit_id", "platform"])
    counts = pd.crosstab(manifest["platform"], manifest["split"])
    rows = []
    for platform, label in PLATFORMS.items():
        part = coded[coded["platform"].eq(platform)]
        rows.append([label, *(str(counts.loc[platform, split]) for split in ["pilot", "pilot2", "dev", "test"]),
                     str(int(part["split"].eq("dev").sum())), str(int(part["split"].eq("test").sum())),
                     str(int(part["annotator"].eq("IS").sum())), str(int(part["annotator"].eq("JP").sum()))])
    header = ["Platforma", "pilot", "pilot2", "dev", "test", "dev zakod.", "test zakod.", "IS", "JP"]
    return tabular(header, rows, "l" + "r" * 8)


def categories_table() -> str:
    codebook = load_codebook()
    rows = [[code(category.code), escape(category.name)] for category in codebook.categories]
    return tabular(["Kod", "Kategoria"], rows, "ll")


def pilot_table() -> str:
    table = pd.read_csv(AGREEMENT_DIR / "pilot_agreement.csv")
    table = table[~table["variable"].str.startswith("source_types:")]
    rows = []
    for row in table.itertuples(index=False):
        label = code(row.variable) + (" (MASI)" if row.variable == "source_types" else "")
        rows.append([PLATFORMS[row.platform], label, str(row.units), number(row.observed_agreement),
                     number(row.alpha) + " " + interval(row.alpha_low, row.alpha_high), escape(row.verdict)])
    return tabular(["", "Zmienna", "$n$", "Zgodność", r"$\alpha$ [95\% CI]", "Ocena"], rows, "llrrll", groups=[2])


def annotator_table(path) -> str:
    table = pd.read_csv(path)
    instruments = [name for name in INSTRUMENTS if name in set(table["instrument"]) and name != "refs_v1"]
    specs = [("reddit", "source_types", "masi", "MASI"), ("reddit", "cites_source", "f1", "F1 " + code("cites_source")),
             ("wikipedia", "source_types", "masi", "MASI"), ("wikipedia", "cites_source", "f1", "F1 " + code("cites_source"))]
    rows = []
    for platform, variable, name, label in specs:
        cells = []
        for instrument in instruments:
            for subset in ["IS", "JP"]:
                row = metric(table, instrument, platform, variable, name, subset)
                cells.append("--" if row is None else number(row["value"]))
        rows.append([PLATFORMS[platform], label, *cells])
    header = ["", "Miara", *(rf"\multicolumn{{2}}{{c}}{{{INSTRUMENTS[name]}}}" for name in instruments)]
    subheader = " & ".join(["", "", *(["IS", "JP"] * len(instruments))]) + r" \\"
    text = tabular(header, rows, "ll" + "cc" * len(instruments), groups=[2])
    return text.replace(r"\midrule", subheader + "\n" + r"\midrule", 1)


def errors_table() -> str:
    table = pd.read_csv(ERRORS_DIR / "dev_pareto.csv")
    rows = []
    for instrument in [name for name in INSTRUMENTS if name in set(table["instrument"])]:
        part = table[table["instrument"].eq(instrument)]
        top = ", ".join(f"{escape(row.cause)} ({row.errors})" for row in part.head(3).itertuples(index=False))
        rows.append([INSTRUMENTS[instrument], str(int(part["errors"].sum())), str(int(part["confirmed"].sum())), top])
    return tabular(["Instrument", "Błędy", "Potwierdzone", "Najczęstsze proponowane przyczyny"], rows, "lrrp{8.2cm}")


def differential_table() -> str:
    table = pd.read_csv(ERRORS_DIR / "differential_test.csv")
    table = table[table["variable"].eq("cites_source")]
    tests = table.drop_duplicates(["instrument", "platform", "grouping", "rate"]).set_index(["instrument", "platform", "grouping", "rate"])
    rows = []
    for instrument in [name for name in INSTRUMENTS if name in set(table["instrument"])]:
        for platform, label in PLATFORMS.items():
            cells = []
            for grouping in ["period", "source"]:
                for rate in ["false_positive_rate", "false_negative_rate"]:
                    key = (instrument, platform, grouping, rate)
                    cells.append(p_value(tests.loc[key, "p_permutation"]) if key in tests.index else "--")
            rows.append([INSTRUMENTS[instrument], label, *cells])
    header = ["Instrument", "", "okres: FP", "okres: FN", "grupa: FP", "grupa: FN"]
    return tabular(header, rows, "llcccc", groups=list(range(2, len(rows), 2)))


def kappa_table() -> str:
    table = pd.read_csv(VALIDATION_DIR / "comparison_kappa.csv")
    rows = []
    for row in table.itertuples(index=False):
        rater = "annotatorzy (pilotaż)" if row.rater.startswith("annotators") else INSTRUMENTS.get(row.rater, escape(row.rater))
        rows.append([PLATFORMS[row.platform], code(row.variable), rater, str(int(row.units)),
                     number(row.kappa) + " " + interval(row.low, row.high), number(row.agreement)])
    groups = [index for index in range(1, len(rows)) if table.iloc[index][["platform", "variable"]].tolist() != table.iloc[index - 1][["platform", "variable"]].tolist()]
    return tabular(["", "Zmienna", "Kto", "$n$", r"$\kappa$ [95\% CI]", "Zgodność"], rows, "lllrll", groups=groups)


def mcnemar_table() -> str:
    table = pd.read_csv(VALIDATION_DIR / "comparison_mcnemar.csv")
    rows = [[PLATFORMS[row.platform], f"{INSTRUMENTS[row.first]} vs {INSTRUMENTS[row.second]}", str(row.units),
             str(row.only_first_right), str(row.only_second_right), p_value(row.p_exact)]
            for row in table.sort_values(["platform"], kind="stable").itertuples(index=False)]
    header = ["", "Para (A vs B)", "$n$", "tylko A trafnie", "tylko B trafnie", "$p$ dokładne"]
    return tabular(header, rows, "llrrrr", groups=[sum(table["platform"].eq("reddit"))])


def rankings_table() -> str:
    table = pd.read_csv(VALIDATION_DIR / "comparison_rankings.csv")
    rows = [[PLATFORMS[row.platform], INSTRUMENTS[row.source], number(row.kendall_tau), p_value(row.p_value),
             "tak" if row.same_top_category else "nie"] for row in table.itertuples(index=False)]
    return tabular(["", "Instrument", r"$\tau_b$", "$p$", "Ta sama kategoria nr 1"], rows, "llrrl",
                   groups=[sum(table["platform"].eq("reddit"))])


def shares_table() -> str:
    table = pd.read_csv(VALIDATION_DIR / "gold_shares.csv").set_index(["variable", "platform"])
    variables = list(dict.fromkeys(table.index.get_level_values("variable")))
    rows = []
    for variable in variables:
        cells = []
        for platform in PLATFORMS:
            row = table.loc[(variable, platform)]
            cells.append(f"{number(row['share'])} {interval(row['low'], row['high'])}")
        rows.append([code(variable), *cells])
    units = [str(int(table.xs(platform, level="platform")["units"].iloc[0])) for platform in PLATFORMS]
    header = ["", f"Reddit ($n$ = {units[0]})", f"Wikipedia ($n$ = {units[1]})"]
    return tabular(header, rows, "lll", groups=[1])


def h1b_table() -> str:
    table = pd.read_csv(HYPOTHESES_DIR / "confirmatory_trends.csv")
    table = table[table["hypothesis"].eq("H1-B")]
    rows = []
    for outcome, label in H1_OUTCOMES.items():
        for analysis, name in H1_ANALYSES.items():
            row = table[table["outcome"].eq(outcome) & table["analysis"].eq(analysis)].iloc[0]
            rows.append([label if analysis == "primary" else "", name, str(row["units"]), str(row["positives"]),
                         number(row["odds_ratio_per_year"]) + " " + interval(row["ci_low"], row["ci_high"]), p_value(row["p_one_sided"])])
    return tabular(["Wskaźnik", "Analiza", "Posty", "Z kategorią", "OR/rok [95\\% CI]", "$p$ jednostr."], rows, "llrrlr", groups=[4])


def h2_table() -> str:
    table = pd.read_csv(HYPOTHESES_DIR / "confirmatory_trends.csv")
    table = table[table["hypothesis"].eq("H2")]
    rows = []
    for analysis, name in H2_ANALYSES.items():
        row = table[table["analysis"].eq(analysis)].iloc[0]
        rows.append([name, str(row["units"]), str(row["positives"]),
                     number(row["odds_ratio_per_year"]) + " " + interval(row["ci_low"], row["ci_high"]), p_value(row["p_one_sided"])])
    permutation = json.loads((HYPOTHESES_DIR / "exploratory_h2_permutation.json").read_text(encoding="utf-8"))
    rows.append([r"\textit{permutacja lat (eksploracyjna)}", "", "", "", p_value(permutation.get("p_one_sided", np.nan))])
    return tabular(["Analiza", "Linki", "Alternatywne", "OR/rok [95\\% CI]", "$p$ jednostr."], rows, "lrrlr")


def h2_robustness_table() -> str:
    table = pd.read_csv(HYPOTHESES_DIR / "exploratory_h2_robustness.csv")
    exact = json.loads((HYPOTHESES_DIR / "exploratory_h2_exact_by_owner.json").read_text(encoding="utf-8"))
    rows = []
    for row in table.itertuples(index=False):
        rows.append([ROBUSTNESS.get(row.analysis, escape(row.analysis)), row.measure,
                     number(row.ratio_per_year) + " " + interval(row.ci_low, row.ci_high), p_value(row.p_one_sided), str(row.events)])
    rows.append(["właściciel posta, dokładny test warunkowy", "--", "--", p_value(exact["p_one_sided"]), "2"])
    groups = [index for index, row in enumerate(table.itertuples(index=False)) if row.analysis.startswith(("measurement:", "Firth, all"))][:2]
    return tabular(["Analiza", "Miara", "Efekt/rok [95\\% CI]", "$p$ jednostr.", "Zdarzenia"], rows, "p{6.4cm}lllr", groups=groups)


def yearly_figure() -> None:
    """Yearly weighted shares with 95% intervals: H1-B consensus and alternative sources, H2 alternative links."""
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter, MaxNLocator

    yearly = pd.read_csv(HYPOTHESES_DIR / "confirmatory_yearly.csv")
    yearly = yearly[yearly["group"].eq("all")]
    panels = [("H1-B", "consensus", "H1-B: źródła konsensusu (Reddit)"),
              ("H1-B", "alternative", "H1-B: źródła alternatywne (Reddit)"),
              ("H2", "alternative", "H2: linki alternatywne w przypisach (Wikipedia)")]
    figure, axes = plt.subplots(1, 3, figsize=(13, 3.4), facecolor=SURFACE)
    for axis, (hypothesis, outcome, title) in zip(axes, panels):
        part = yearly[yearly["hypothesis"].eq(hypothesis) & yearly["outcome"].eq(outcome)].sort_values("year")
        axis.set_facecolor(SURFACE)
        axis.fill_between(part["year"], part["low"], part["high"], color=SERIES, alpha=0.12, linewidth=0)
        axis.plot(part["year"], part["share"], color=SERIES, linewidth=2, solid_capstyle="round", zorder=3)
        axis.plot(part["year"], part["share"], "o", color=SERIES, markersize=6, markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=4,
                  clip_on=False)
        axis.set_ylim(0, max(part["high"].max(), part["share"].max()) * 1.1)
        axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:.0%}".replace("%", " %")))
        axis.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=7))
        axis.grid(axis="y", color=GRID, linewidth=0.8)
        axis.set_axisbelow(True)
        axis.tick_params(colors=INK_SECONDARY, length=0, labelsize=8)
        for side in ["top", "right", "left"]:
            axis.spines[side].set_visible(False)
        axis.spines["bottom"].set_color(GRID)
        axis.set_title(title, loc="left", fontsize=10, color=INK)
    figure.supxlabel("rok; udział ważony z 95% przedziałem bootstrap", fontsize=8, color=INK_SECONDARY)
    figure.tight_layout()
    figure.savefig(FIGURES_DIR / "yearly_shares.png", dpi=200, facecolor=SURFACE)


def main() -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    write("sample", sample_table())
    write("categories", categories_table())
    write("pilot_agreement", pilot_table())
    write("test_metrics", metric_table(VALIDATION_DIR / "test_metrics.csv"))
    write("dev_metrics", metric_table(VALIDATION_DIR / "dev_metrics.csv"))
    write("annotators", annotator_table(VALIDATION_DIR / "test_metrics.csv"))
    write("errors", errors_table())
    write("differential", differential_table())
    write("kappa", kappa_table())
    write("mcnemar", mcnemar_table())
    write("rankings", rankings_table())
    write("gold_shares", shares_table())
    write("h1b", h1b_table())
    write("h2", h2_table())
    write("h2_robustness", h2_robustness_table())
    for source, name in [(AGREEMENT_DIR / "pilot_alpha.png", "pilot_alpha.png"), (ERRORS_DIR / "dev_pareto.png", "dev_pareto.png")]:
        shutil.copyfile(source, FIGURES_DIR / name)
    yearly_figure()
    print(f"Tables -> {TABLES_DIR}, figures -> {FIGURES_DIR}")


if __name__ == "__main__":
    main()
