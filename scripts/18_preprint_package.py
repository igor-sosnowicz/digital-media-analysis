"""Results package of the v1-based preprint: number macros, two compact tables and four figures.

Everything comes from the saved result files (and, for the H2 figure, from the
local Wikipedia download the H2 test read); nothing is estimated anew except
the exploratory shift-share split of the H1-B change, computed from the
analysis sample and its labels. Writes:
- report/numbers.tex: one macro per number the text cites (`\\res...`), so the
  prose follows the results; docs/podsumowanie_wynikow.md lists them by section;
- report/tables/preprint_data.tex (data, sample, agreement) and
  preprint_h2.tex (H2: preregistered test, robustness, measurement check);
  the preprint also uses test_metrics.tex and h1b.tex from scripts/13;
- report/figures/preprint_instruments.png, preprint_h1.png, preprint_h2.png,
  preprint_agreement.png.
"""

import json

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from digital_media_analysis import adjudication, annotations, gold, hypotheses, inference, owners, wikipedia_refs  # noqa: E402
from digital_media_analysis.agreement import ALPHA_RELIABLE, ALPHA_TENTATIVE, GRID, INK, INK_SECONDARY, SERIES, SURFACE  # noqa: E402
from digital_media_analysis.charts import CATEGORICAL, MUTED  # noqa: E402
from digital_media_analysis.config_reader import get_hypotheses  # noqa: E402
from digital_media_analysis.paths import (  # noqa: E402
    AGREEMENT_DIR,
    ANNOTATIONS_DIR,
    ERRORS_DIR,
    FRAME_LABELS_DIR,
    HYPOTHESES_DIR,
    PROJECT_ROOT,
    VALIDATION_DIR,
)
from digital_media_analysis.report import code, interval, macro_file, number, p_value, tabular  # noqa: E402

REPORT_DIR = PROJECT_ROOT / "report"
INSTRUMENTS = {"rules_v1": "v1", "zeroshot_v1": "zero-shot", "gliner_v1": "GLiNER"}
PLATFORMS = {"reddit": "Reddit", "wikipedia": "Wikipedia"}


def count(value) -> str:
    """An integer with a thin space every three digits from 10 000 on, as Polish typesetting has it."""
    value = int(value)
    return f"{value:,}".replace(",", "\\,") if value >= 10_000 else str(value)


def percent(value: float, digits: int = 0) -> str:
    return number(100 * value, digits) + "\\,\\%"


def both(value: float, low: float, high: float, digits: int = 2) -> str:
    return f"{number(value, digits)} {interval(low, high, digits)}".strip()


class Numbers(dict):
    def put(self, key: str, value) -> None:
        if key in self:
            raise ValueError(f"Duplicate key {key}")
        self[key] = value


def metric(table: pd.DataFrame, instrument: str, platform: str, variable: str, name: str, subset: str = "all") -> pd.Series:
    rows = table[(table["instrument"] == instrument) & (table["platform"] == platform) & (table["subset"] == subset)
                 & (table["variable"] == variable) & (table["metric"] == name)]
    if rows.empty:
        raise KeyError((instrument, platform, variable, name, subset))
    return rows.iloc[0]


def data_numbers(numbers: Numbers) -> pd.DataFrame:
    design = json.loads((ANNOTATIONS_DIR / "sample_design.json").read_text(encoding="utf-8"))
    manifest = gold.load_manifest()
    splits = pd.crosstab(manifest["platform"], manifest["split"])
    reference, _ = annotations.gold_reference(annotations.load_labels("gold"), adjudication.load_decisions("gold"))
    coded = reference.merge(manifest[["unit_id", "platform", "split"]], on=["unit_id", "platform"])
    for platform in PLATFORMS:
        numbers.put(f"{platform} frame", count(design["population"][platform]["units"]))
        for split in ["pilot", "pilot2", "dev", "test"]:
            numbers.put(f"{platform} {split.replace('2', ' two')}", count(splits.loc[platform, split]))
        part = coded[coded["platform"].eq(platform)]
        numbers.put(f"{platform} coded dev", count(part["split"].eq("dev").sum()))
        numbers.put(f"{platform} coded test", count(part["split"].eq("test").sum()))
        test = part[part["split"].eq("test")]
        numbers.put(f"{platform} test citing", count(test["cites_source"].astype(int).sum()))
    gold_labels = annotations.load_labels("gold")
    for annotator in ["IS", "JP"]:
        numbers.put(f"gold labels {annotator}", count(gold_labels["annotator"].eq(annotator).sum()))
    return coded


def agreement_numbers(numbers: Numbers) -> pd.DataFrame:
    table = pd.read_csv(AGREEMENT_DIR / "pilot_agreement.csv")
    rows = table.set_index(["platform", "variable"])
    for (platform, variable), key in [(("reddit", "cites_source"), "reddit cites"), (("reddit", "source_types"), "reddit masi"),
                                      (("wikipedia", "cites_source"), "wikipedia cites"), (("wikipedia", "edit_about_sources"), "wikipedia edit"),
                                      (("wikipedia", "source_types"), "wikipedia masi")]:
        row = rows.loc[(platform, variable)]
        numbers.put(f"pilot {key} alpha", both(row["alpha"], row["alpha_low"], row["alpha_high"]))
        numbers.put(f"pilot {key} agreement", number(row["observed_agreement"]))
    numbers.put("pilot reddit units", count(rows.loc[("reddit", "cites_source"), "units"]))
    numbers.put("pilot wikipedia units", count(rows.loc[("wikipedia", "cites_source"), "units"]))
    numbers.put("pilot disputes", count(len(adjudication.disputed(annotations.load_labels("pilot")))))
    summary = pd.read_csv(AGREEMENT_DIR / "pilot_annotators.csv").set_index(["platform", "annotator"])
    numbers.put("pilot reddit IS citing share", percent(summary.loc[("reddit", "IS"), "cites_share"]))
    return table


def instrument_numbers(numbers: Numbers) -> None:
    test = pd.read_csv(VALIDATION_DIR / "test_metrics.csv")
    for instrument in INSTRUMENTS:
        name = instrument.split("_")[0]
        for platform in PLATFORMS:
            row = metric(test, instrument, platform, "cites_source", "f1")
            numbers.put(f"test {name} {platform} cites f", both(row["value"], row["low"], row["high"]))
            numbers.put(f"test {name} {platform} cites kappa", number(metric(test, instrument, platform, "cites_source", "kappa")["value"]))
            row = metric(test, instrument, platform, "source_types", "masi")
            numbers.put(f"test {name} {platform} masi", both(row["value"], row["low"], row["high"]))
        row = metric(test, instrument, "reddit", "source_types", "macro_f1")
        numbers.put(f"test {name} reddit macro f", both(row["value"], row["low"], row["high"]))
    row = metric(test, "zeroshot_v1", "wikipedia", "edit_about_sources", "f1")
    numbers.put("test zeroshot wikipedia edit f", both(row["value"], row["low"], row["high"]))
    for variable, key in [("precision", "precision"), ("recall", "recall")]:
        numbers.put(f"test gliner reddit cites {key}", number(metric(test, "gliner_v1", "reddit", "cites_source", variable)["value"]))
    for code_name in ["media", "social_blog"]:
        numbers.put(f"test gliner reddit {code_name.replace('_', ' ')} f", number(metric(test, "gliner_v1", "reddit", f"source_types:{code_name}", "f1")["value"]))
    for subset in ["IS", "JP"]:
        numbers.put(f"test gliner reddit masi {subset}", number(metric(test, "gliner_v1", "reddit", "source_types", "masi", subset)["value"]))
        numbers.put(f"test gliner wikipedia cites f {subset}", number(metric(test, "gliner_v1", "wikipedia", "cites_source", "f1", subset)["value"]))
    dev = pd.read_csv(VALIDATION_DIR / "dev_metrics.csv")
    numbers.put("dev gliner reddit masi", number(metric(dev, "gliner_v1", "reddit", "source_types", "masi")["value"]))
    numbers.put("dev rulesvtwo reddit masi", number(metric(dev, "rules_v2", "reddit", "source_types", "masi")["value"]))
    numbers.put("dev rulesvtwo wikipedia edit f", number(metric(dev, "rules_v2", "wikipedia", "edit_about_sources", "f1")["value"]))
    numbers.put("dev refs wikipedia edit f", number(metric(dev, "refs_v1", "wikipedia", "edit_about_sources", "f1")["value"]))
    mcnemar = pd.read_csv(VALIDATION_DIR / "comparison_mcnemar.csv").set_index(["platform", "first", "second"])
    for (platform, first, second), key in [(("reddit", "zeroshot_v1", "gliner_v1"), "reddit zeroshot gliner"),
                                           (("wikipedia", "zeroshot_v1", "gliner_v1"), "wikipedia zeroshot gliner"),
                                           (("reddit", "rules_v1", "gliner_v1"), "reddit vone gliner")]:
        row = mcnemar.loc[(platform, first, second)]
        numbers.put(f"mcnemar {key} only first", count(row["only_first_right"]))
        numbers.put(f"mcnemar {key} only second", count(row["only_second_right"]))
        numbers.put(f"mcnemar {key} p", p_value(row["p_exact"]))
    rankings = pd.read_csv(VALIDATION_DIR / "comparison_rankings.csv").set_index(["platform", "source"])
    numbers.put("tau gliner reddit", number(rankings.loc[("reddit", "gliner_v1"), "kendall_tau"]))
    numbers.put("tau gliner reddit p", p_value(rankings.loc[("reddit", "gliner_v1"), "p_value"]))
    shares = pd.read_csv(VALIDATION_DIR / "gold_shares.csv").set_index(["platform", "variable"])
    for platform, variable in [("reddit", "cites_source"), ("reddit", "media"), ("reddit", "social_blog"),
                               ("wikipedia", "cites_source"), ("wikipedia", "personal")]:
        row = shares.loc[(platform, variable)]
        numbers.put(f"gold share {platform} {variable.replace('_', ' ')}", both(row["share"], row["low"], row["high"]))
    pareto = pd.read_csv(ERRORS_DIR / "dev_pareto.csv")
    for instrument, key in [("rules_v1", "vone"), ("gliner_v1", "gliner"), ("rules_v2", "rulesvtwo")]:
        numbers.put(f"errors {key} total", count(pareto.loc[pareto["instrument"].eq(instrument), "errors"].sum()))
    url = pareto[pareto["instrument"].eq("rules_v1") & pareto["cause"].str.startswith("pominięte")].iloc[0]
    numbers.put("errors vone url", count(url["errors"]))
    numbers.put("errors vone url share", percent(url["share"]))
    differential = pd.read_csv(ERRORS_DIR / "differential_test.csv")
    tests = differential.drop_duplicates(["instrument", "platform", "variable", "grouping", "rate"]).set_index(
        ["instrument", "platform", "variable", "grouping", "rate"])["p_permutation"]
    numbers.put("differential gliner reddit period fp p", p_value(tests.loc[("gliner_v1", "reddit", "cites_source", "period", "false_positive_rate")]))
    numbers.put("differential gliner reddit subreddit fp p", p_value(tests.loc[("gliner_v1", "reddit", "cites_source", "source", "false_positive_rate")]))


def h1_frame() -> pd.DataFrame:
    settings = get_hypotheses()["h1"]
    sample = pd.read_csv(HYPOTHESES_DIR / "h1_sample.csv", dtype={"unit_id": str})
    labels = pd.read_csv(FRAME_LABELS_DIR / "h1_gliner_v1.csv", dtype={"unit_id": str})
    frame = hypotheses.h1b_outcomes(sample.merge(labels, on="unit_id"), settings["consensus_sources"], settings["alternative_sources"])
    return hypotheses.in_years(frame, settings["period"]).reset_index(drop=True)


def h1_numbers(numbers: Numbers, frame: pd.DataFrame) -> dict:
    trends = pd.read_csv(HYPOTHESES_DIR / "confirmatory_trends.csv")
    numbers.put("hone sample", count(len(pd.read_csv(HYPOTHESES_DIR / "h1_sample.csv"))))
    rows = trends[trends["hypothesis"].eq("H1-B")].set_index(["analysis", "outcome"])
    numbers.put("hone b citing", count(rows.loc[("primary", "consensus"), "units"]))
    for analysis, label in [("primary", ""), ("sensitivity_period", " twenty"), ("only_science", " science"), ("only_conspiracy", " conspiracy")]:
        for outcome in ["consensus", "alternative"]:
            row = rows.loc[(analysis, outcome)]
            numbers.put(f"hone b {outcome}{label} or", both(row["odds_ratio_per_year"], row["ci_low"], row["ci_high"]))
            numbers.put(f"hone b {outcome}{label} p", p_value(row["p_one_sided"]))
    yearly = pd.read_csv(HYPOTHESES_DIR / "confirmatory_yearly.csv")
    yearly = yearly[yearly["hypothesis"].eq("H1-B") & yearly["group"].eq("all")].pivot(index="year", columns="outcome", values="share")
    numbers.put("hone b consensus share twothousandsix", percent(yearly.loc[2006, "consensus"]))
    numbers.put("hone b consensus share late low", percent(yearly.loc[2016:2018, "consensus"].min()))
    numbers.put("hone b consensus share late high", percent(yearly.loc[2016:2018, "consensus"].max()))
    numbers.put("hone b alternative share twothousandfive", percent(yearly.loc[2005, "alternative"]))
    numbers.put("hone b alternative share late high", percent(yearly.loc[2016:2018, "alternative"].max()))
    weights = frame.groupby(["year", "group"])["weight"].sum().unstack(fill_value=0)
    shares = weights.div(weights.sum(axis=1), axis=0)
    numbers.put("hone conspiracy share twothousandeight", percent(shares.loc[2008, "conspiracy"]))
    numbers.put("hone conspiracy share twothousandeighteen", percent(shares.loc[2018, "conspiracy"]))
    decomposition = {}
    for outcome in ["consensus", "alternative"]:
        parts = inference.shift_share(frame, outcome, "group", [2005, 2009], [2014, 2018])
        decomposition[outcome] = parts
        for part in ["total", "within", "composition"]:
            numbers.put(f"hone b {outcome} shift {part}", number(100 * parts[part], 1).replace("{,}", "{,}") + "\\,pp")
    return decomposition


def h2_links() -> pd.DataFrame:
    settings = get_hypotheses()["h2"]
    links = hypotheses.h2_outcomes(wikipedia_refs.load_added_links(), settings["period"], settings["alternative_categories"])
    links = links.reset_index(drop=True)
    _, accounts = owners.load_owner_types()
    found = owners.classify(links["url"], accounts)
    first = ~links.sort_values("revision_number").duplicated(["page", "url"]).sort_index()
    return links.assign(owner_type=found["owner_type"], first_addition=first)


def h2_numbers(numbers: Numbers, links: pd.DataFrame) -> None:
    trends = pd.read_csv(HYPOTHESES_DIR / "confirmatory_trends.csv")
    rows = trends[trends["hypothesis"].eq("H2")].set_index("analysis")
    alternative = links[links["alternative"].eq(1)]
    numbers.put("htwo links", count(len(links)))
    numbers.put("htwo alternative links", count(len(alternative)))
    numbers.put("htwo model links", count(rows.loc["primary", "units"]))
    numbers.put("htwo alternative pages", count(alternative["page"].nunique()))
    official = alternative["owner_type"].eq("institution")
    numbers.put("htwo official links", count(official.sum()))
    numbers.put("htwo who repeats", count(alternative["url"].str.contains("pscp.tv/WHO", case=False).sum()))
    numbers.put("htwo by owner links", count((~official).sum()))
    for analysis, key in [("primary", ""), ("without_covid19", " without covid"), ("without_2020", " without twentytwenty"),
                          ("classified_only", " classified")]:
        row = rows.loc[analysis]
        numbers.put(f"htwo{key} or", both(row["odds_ratio_per_year"], row["ci_low"], row["ci_high"]))
        numbers.put(f"htwo{key} p", p_value(row["p_one_sided"]))
    permutation = json.loads((HYPOTHESES_DIR / "exploratory_h2_permutation.json").read_text(encoding="utf-8"))
    numbers.put("htwo permutation p", p_value(permutation["p_one_sided"]))
    robustness = pd.read_csv(HYPOTHESES_DIR / "exploratory_h2_robustness.csv").set_index("analysis")
    for analysis, key in [("Firth, all pages", "firth"), ("measurement: first addition of each link only", "first"),
                          ("measurement: owner of the post (WHO, GIS posts are institutional)", "owner")]:
        row = robustness.loc[analysis]
        numbers.put(f"htwo {key} or", both(row["ratio_per_year"], row["ci_low"], row["ci_high"]))
        numbers.put(f"htwo {key} p", p_value(row["p_one_sided"]))
        numbers.put(f"htwo {key} events", count(row["events"]))
    exact = json.loads((HYPOTHESES_DIR / "exploratory_h2_exact_by_owner.json").read_text(encoding="utf-8"))
    numbers.put("htwo exact p", p_value(exact["p_one_sided"]))


def data_table(coded: pd.DataFrame, agreement_table: pd.DataFrame, numbers: Numbers) -> str:
    rows = []
    agree = agreement_table.set_index(["platform", "variable"])
    for platform, label in PLATFORMS.items():
        rows.append([label, numbers[f"{platform} frame"],
                     f"{numbers[f'{platform} pilot']} / {numbers[f'{platform} dev']} / {numbers[f'{platform} test']}",
                     f"{numbers[f'{platform} coded dev']} / {numbers[f'{platform} coded test']}",
                     count(agree.loc[(platform, "cites_source"), "units"]),
                     both(agree.loc[(platform, "cites_source"), "alpha"], np.nan, np.nan),
                     both(agree.loc[(platform, "source_types"), "alpha"], np.nan, np.nan)])
    header = ["", "Rama", "Próba: pilotaż / dev / test", "Gold: dev / test", "Pilotaż (2 osoby)",
              r"$\alpha$ " + code("cites_source"), r"$\alpha$ typy (MASI)"]
    return tabular(header, rows, "lrcccrr")


def h2_table() -> str:
    trends = pd.read_csv(HYPOTHESES_DIR / "confirmatory_trends.csv")
    rows_h2 = trends[trends["hypothesis"].eq("H2")].set_index("analysis")
    robustness = pd.read_csv(HYPOTHESES_DIR / "exploratory_h2_robustness.csv").set_index("analysis")
    permutation = json.loads((HYPOTHESES_DIR / "exploratory_h2_permutation.json").read_text(encoding="utf-8"))
    exact = json.loads((HYPOTHESES_DIR / "exploratory_h2_exact_by_owner.json").read_text(encoding="utf-8"))
    rows = []
    for analysis, label in [("primary", "test główny"), ("without_covid19", "bez strony COVID-19"), ("without_2020", "bez roku 2020")]:
        row = rows_h2.loc[analysis]
        rows.append(["preregistrowane", label, both(row["odds_ratio_per_year"], row["ci_low"], row["ci_high"]),
                     p_value(row["p_one_sided"]), count(row["positives"])])
    rows.append(["eksploracyjne", "permutacja lat między rewizjami", "--", p_value(permutation["p_one_sided"]), "10"])
    for analysis, label in [("Firth, all pages", "logit Firtha, wszystkie strony"),
                            ("measurement: first addition of each link only", "tylko pierwsze dodanie linku"),
                            ("measurement: owner of the post (WHO, GIS posts are institutional)", "według właściciela konta (Firth)")]:
        row = robustness.loc[analysis]
        rows.append(["eksploracyjne", label, both(row["ratio_per_year"], row["ci_low"], row["ci_high"]), p_value(row["p_one_sided"]),
                     count(row["events"])])
    rows.append(["eksploracyjne", "według właściciela, test dokładny", "--", p_value(exact["p_one_sided"]), "2"])
    return tabular(["", "Analiza", "OR/rok [95\\% CI]", "$p$ jednostr.", "Zdarzenia"], rows, "lllrr", groups=[3])


def _axes(axis, grid: str = "x") -> None:
    axis.set_facecolor(SURFACE)
    axis.grid(axis=grid, color=GRID, linewidth=0.8)
    axis.set_axisbelow(True)
    axis.tick_params(colors=INK_SECONDARY, length=0, labelsize=8)
    for side in ["top", "right", "left"]:
        axis.spines[side].set_visible(False)
    axis.spines["bottom"].set_color(GRID)


def figure_instruments(path) -> None:
    """Test metrics of the three frozen instruments: dot and interval per metric, one panel per platform."""
    import matplotlib.pyplot as plt

    test = pd.read_csv(VALIDATION_DIR / "test_metrics.csv")
    panels = {"reddit": [("cites_source", "f1", "F1 cites_source"), ("source_types", "masi", "MASI (typy)"),
                         ("source_types", "macro_f1", "macro-F1 (typy)")],
              "wikipedia": [("cites_source", "f1", "F1 cites_source"), ("edit_about_sources", "f1", "F1 edit_about_sources"),
                            ("source_types", "masi", "MASI (typy)")]}
    figure, axes = plt.subplots(1, 2, figsize=(10, 3.3), sharex=True, facecolor=SURFACE)
    offsets = dict(zip(INSTRUMENTS, [0.22, 0.0, -0.22]))
    for axis, (platform, specs) in zip(axes, panels.items()):
        _axes(axis)
        for position, (variable, name, _) in zip(range(len(specs))[::-1], specs):
            for colour, instrument in zip(CATEGORICAL, INSTRUMENTS):
                rows = test[(test["instrument"] == instrument) & (test["platform"] == platform) & (test["subset"] == "all")
                            & (test["variable"] == variable) & (test["metric"] == name)]
                if rows.empty or not np.isfinite(rows.iloc[0]["value"]):
                    continue
                row = rows.iloc[0]
                y = position + offsets[instrument]
                if np.isfinite(row["low"]):
                    axis.hlines(y, row["low"], row["high"], color=colour, linewidth=2)
                axis.plot(row["value"], y, "o", color=colour, markersize=6, markeredgecolor=SURFACE, markeredgewidth=1.5,
                          label=INSTRUMENTS[instrument] if position == len(specs) - 1 else None)
        axis.set_yticks(range(len(specs))[::-1])
        axis.set_yticklabels([label for _, _, label in specs], fontsize=8, color=INK)
        axis.set_xlim(0, 1)
        axis.set_title(f"{PLATFORMS[platform]}: zbiór testowy", loc="left", fontsize=10, color=INK)
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, frameon=False, fontsize=8, labelcolor=INK, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.02))
    figure.supxlabel("wartość miary (ważona) z 95% przedziałem bootstrap", fontsize=8, color=INK_SECONDARY)
    figure.tight_layout(rect=(0, 0, 1, 0.93))
    figure.savefig(path, dpi=200, facecolor=SURFACE)


def figure_h1(frame: pd.DataFrame, path) -> None:
    """H1-B: yearly shares of consensus and alternative sources, and the subreddit make-up of the citing posts."""
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter

    yearly = pd.read_csv(HYPOTHESES_DIR / "confirmatory_yearly.csv")
    yearly = yearly[yearly["hypothesis"].eq("H1-B") & yearly["group"].eq("all")]
    weights = frame.groupby(["year", "group"])["weight"].sum().unstack(fill_value=0)
    shares = weights.div(weights.sum(axis=1), axis=0)
    shares = shares[[name for name in ["reddit.com", "science", "skeptic", "conspiracy"] if name in shares]]
    figure, axes = plt.subplots(1, 3, figsize=(12, 3.3), facecolor=SURFACE)
    formatter = FuncFormatter(lambda value, _: f"{value:.0%}".replace("%", " %"))
    for axis, (outcome, title) in zip(axes[:2], [("consensus", "źródła konsensusu"), ("alternative", "źródła alternatywne")]):
        part = yearly[yearly["outcome"].eq(outcome)].sort_values("year")
        _axes(axis, "y")
        axis.fill_between(part["year"], part["low"], part["high"], color=SERIES, alpha=0.12, linewidth=0)
        axis.plot(part["year"], part["share"], color=SERIES, linewidth=2)
        axis.plot(part["year"], part["share"], "o", color=SERIES, markersize=4, markeredgecolor=SURFACE, clip_on=False)
        axis.set_ylim(0, max(part["high"].max(), 0.1) * 1.1)
        axis.yaxis.set_major_formatter(formatter)
        axis.set_title(f"H1-B: {title}", loc="left", fontsize=9, color=INK)
    axis = axes[2]
    _axes(axis, "y")
    axis.stackplot(shares.index, shares.T.to_numpy(), labels=[f"r/{name}" for name in shares.columns],
                   colors=CATEGORICAL[: shares.shape[1]], edgecolor=SURFACE, linewidth=1.5)
    axis.set_ylim(0, 1)
    axis.set_xlim(shares.index.min(), shares.index.max())
    axis.yaxis.set_major_formatter(formatter)
    axis.set_title("skład próby (udział ważony)", loc="left", fontsize=9, color=INK)
    axis.legend(frameon=False, fontsize=7, labelcolor=INK, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    figure.tight_layout()
    figure.savefig(path, dpi=200, facecolor=SURFACE)


def figure_h2(links: pd.DataFrame, path) -> None:
    """H2: every link counted as alternative, by date and page, coloured by the owner of the account; hollow = re-added."""
    import matplotlib.pyplot as plt

    alternative = links[links["alternative"].eq(1)].copy()
    alternative["when"] = pd.to_datetime(alternative["introduced"], utc=True)
    alternative["owner"] = np.where(alternative["owner_type"].eq("institution"), "konto instytucji (WHO, GIS)", "źródło alternatywne")
    pages = list(dict.fromkeys(alternative.sort_values("page")["page"]))
    figure, axis = plt.subplots(figsize=(9, 2.4), facecolor=SURFACE)
    _axes(axis)
    rng = np.random.default_rng(1)
    for colour, owner in zip([MUTED, CATEGORICAL[1]], ["konto instytucji (WHO, GIS)", "źródło alternatywne"]):
        for first, marker_face in [(True, colour), (False, SURFACE)]:
            part = alternative[alternative["owner"].eq(owner) & alternative["first_addition"].eq(first)]
            if part.empty:
                continue
            y = part["page"].map({page: index for index, page in enumerate(pages)}).to_numpy(float) + rng.uniform(-0.12, 0.12, len(part))
            axis.scatter(part["when"], y, s=48, facecolors=marker_face, edgecolors=colour, linewidths=1.8, zorder=3,
                         label=f"{owner}{'' if first else ', ponowne dodanie'}")
    axis.set_yticks(range(len(pages)))
    axis.set_yticklabels(pages, fontsize=8, color=INK)
    axis.set_ylim(-0.6, len(pages) - 0.4)
    axis.set_title("H2: wszystkie linki „alternatywne” dodane do przypisów w latach 2020–2026", loc="left", fontsize=9, color=INK)
    axis.legend(frameon=False, fontsize=7, labelcolor=INK, loc="upper left", bbox_to_anchor=(1.0, 1.05))
    figure.tight_layout()
    figure.savefig(path, dpi=200, facecolor=SURFACE)


def figure_agreement(table: pd.DataFrame, path) -> None:
    """Pilot agreement of the two annotators for the headline variables, with Krippendorff's thresholds."""
    import matplotlib.pyplot as plt

    specs = [("reddit", "cites_source", "Reddit: cites_source"), ("reddit", "source_types", "Reddit: typy (MASI)"),
             ("wikipedia", "cites_source", "Wikipedia: cites_source"), ("wikipedia", "edit_about_sources", "Wikipedia: edit_about_sources"),
             ("wikipedia", "source_types", "Wikipedia: typy (MASI)")]
    rows = table.set_index(["platform", "variable"])
    figure, axis = plt.subplots(figsize=(7.5, 2.6), facecolor=SURFACE)
    _axes(axis)
    for threshold in [ALPHA_TENTATIVE, ALPHA_RELIABLE]:
        axis.axvline(threshold, color=INK_SECONDARY, linewidth=1, linestyle=(0, (4, 3)))
        axis.text(threshold, len(specs) - 0.45, f"{threshold:.3g}".replace(".", ","), ha="center", fontsize=7, color=INK_SECONDARY)
    for position, (platform, variable, label) in zip(range(len(specs))[::-1], specs):
        row = rows.loc[(platform, variable)]
        axis.hlines(position, row["alpha_low"], row["alpha_high"], color=SERIES, linewidth=2)
        axis.plot(row["alpha"], position, "o", color=SERIES, markersize=7, markeredgecolor=SURFACE, markeredgewidth=2)
        axis.text(1.04, position, f"zgodność {row['observed_agreement']:.0%}, n = {int(row['units'])}".replace("%", " %"),
                  va="center", fontsize=7, color=INK_SECONDARY)
    axis.set_yticks(range(len(specs))[::-1])
    axis.set_yticklabels([label for _, _, label in specs], fontsize=8, color=INK)
    axis.set_xlim(-0.3, 1.0)
    axis.set_xlabel("α Krippendorffa z 95% przedziałem bootstrap (pilotaż, 2 osoby)", fontsize=8, color=INK_SECONDARY)
    figure.tight_layout()
    figure.savefig(path, dpi=200, facecolor=SURFACE, bbox_inches="tight")


def main() -> None:
    numbers = Numbers()
    coded = data_numbers(numbers)
    agreement_table = agreement_numbers(numbers)
    instrument_numbers(numbers)
    frame = h1_frame()
    h1_numbers(numbers, frame)
    links = h2_links()
    h2_numbers(numbers, links)
    (REPORT_DIR / "numbers.tex").write_text(macro_file(numbers, "scripts/18_preprint_package.py"), encoding="utf-8")
    (REPORT_DIR / "tables").mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "tables" / "preprint_data.tex").write_text(data_table(coded, agreement_table, numbers), encoding="utf-8")
    (REPORT_DIR / "tables" / "preprint_h2.tex").write_text(h2_table(), encoding="utf-8")
    figures = REPORT_DIR / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    figure_instruments(figures / "preprint_instruments.png")
    figure_h1(frame, figures / "preprint_h1.png")
    figure_h2(links, figures / "preprint_h2.png")
    figure_agreement(agreement_table, figures / "preprint_agreement.png")
    print(f"{len(numbers)} numbers -> {REPORT_DIR / 'numbers.tex'}; tables and figures in {REPORT_DIR}")


if __name__ == "__main__":
    main()
