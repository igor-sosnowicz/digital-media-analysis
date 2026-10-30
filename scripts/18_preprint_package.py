"""Results package of the v1-based preprint: number macros, two compact tables and four figures.

Everything comes from the saved result files (and, for the H2 figure, from the
local Wikipedia download the H2 test read); nothing is estimated anew except
the exploratory shift-share split of the H1-B change, computed from the
analysis sample and its labels. Writes:
- report/numbers.tex: one macro per number the text cites (`\\res...`), so the
  prose follows the results; docs/podsumowanie_wynikow.md lists them by section;
- report/tables/preprint_data.tex (data, sample, agreement), preprint_h1.tex
  (H1-A and H1-B trends side by side), preprint_stance.tex (stance agreement and
  stance_v1 on dev and test), preprint_h2.tex (H2: preregistered test,
  robustness, measurement check) and preprint_test_metrics.tex (test metrics of the source instruments); all in
  English, as the preprint is;
- report/figures/preprint_instruments.png, preprint_h1.png (slide_h1.png: H1-B only, 16:9), preprint_h2.png,
  preprint_agreement.png.
H1-A numbers, its table cells and its figure panel are placeholders (macro
\\resPending) until the H1-A pipeline has run (docs/h1a_kroki.md); rerunning this
script then fills them in.
"""

import json

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from digital_media_analysis import adjudication, annotations, gold, hypotheses, inference, owners, stance, wikipedia_refs  # noqa: E402
from digital_media_analysis.agreement import ALPHA_RELIABLE, ALPHA_TENTATIVE, GRID, INK, INK_SECONDARY, SERIES, SURFACE  # noqa: E402
from digital_media_analysis.charts import CATEGORICAL, MUTED  # noqa: E402
from digital_media_analysis.config_reader import get_hypotheses  # noqa: E402
from digital_media_analysis.paths import (  # noqa: E402
    AGREEMENT_DIR,
    ANNOTATIONS_DIR,
    ERRORS_DIR,
    FRAME_LABELS_DIR,
    HYPOTHESES_DIR,
    LABELS_DIR,
    PREDICTIONS_DIR,
    PROJECT_ROOT,
    VALIDATION_DIR,
)
from digital_media_analysis import report  # noqa: E402
from digital_media_analysis.report import code, macro_file, tabular  # noqa: E402

REPORT_DIR = PROJECT_ROOT / "report"
INSTRUMENTS = {"rules_v1": "v1", "zeroshot_v1": "zero-shot", "gliner_v1": "GLiNER"}
PLATFORMS = {"reddit": "Reddit", "wikipedia": "Wikipedia"}


def number(value: float, digits: int = 2) -> str:
    """A number in English notation (the preprint is in English)."""
    return report.number(value, digits, english=True)


def interval(low: float, high: float, digits: int = 2) -> str:
    return report.interval(low, high, digits, english=True)


def estimate(value: float, low: float, high: float, digits: int = 2) -> str:
    return report.estimate(value, low, high, digits, english=True)


def p_value(value: float) -> str:
    return report.p_value(value, english=True)


def count(value) -> str:
    """An integer with a comma every three digits, as English typesetting has it."""
    return f"{int(value):,}"


def percent(value: float, digits: int = 0) -> str:
    return number(100 * value, digits) + "\\%"


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
    # H2 before the domain review (amendment of 27.10.2026): the run that preceded the move into domains.yaml.
    before_path = HYPOTHESES_DIR / "confirmatory_trends_before_domain_review.csv"
    before = pd.read_csv(before_path) if before_path.exists() else pd.DataFrame(columns=["hypothesis", "analysis"])
    before = before[before["hypothesis"].eq("H2") & before["analysis"].eq("primary")]
    numbers.put("htwo before review or", both(*before[["odds_ratio_per_year", "ci_low", "ci_high"]].iloc[0]) if len(before) else WAITING)
    numbers.put("htwo before review p", p_value(before["p_one_sided"].iloc[0]) if len(before) else WAITING)
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
    # The preregistered descriptive indicator of H2 (scripts/09c_h2_descriptive_gold.py): gold edit summaries citing
    # an alternative, unknown or personal source, over the whole period and the range of the yearly shares.
    gold_path = HYPOTHESES_DIR / "h2_descriptive_gold.csv"
    shares = pd.read_csv(gold_path, dtype={"year": str}) if gold_path.exists() else pd.DataFrame(columns=["year"])
    pooled, yearly = shares[shares["year"].eq("all")], shares[shares["year"].ne("all")]
    if pooled.empty:
        for key in ["htwo gold share", "htwo gold units", "htwo gold share min", "htwo gold share max"]:
            numbers.put(key, WAITING)
        return
    row = pooled.iloc[0]
    numbers.put("htwo gold share", f"{percent(row['share'])} {interval(100 * row['low'], 100 * row['high'], 0)}")
    numbers.put("htwo gold units", count(row["units"]))
    numbers.put("htwo gold share min", percent(yearly["share"].min()))
    numbers.put("htwo gold share max", percent(yearly["share"].max()))


PENDING = r"\resPending"
# The stance pilot people never coded.
NOT_CODED = r"\textit{not coded}"
# H1-A results that will never exist because stance_v1 failed its validity gate.
NOT_TESTED = r"\textit{not tested}"
# The one person who checked every plan C row people were to decide (docs/hipotezy.md, amendment "weryfikacja przez
# człowieka" of 27.10.2026); the sheets record only that a person checked a row, not who.
HUMAN_CHECKER = "JP"
H1_ANALYSES = [("primary", "main (2005--2018)"), ("sensitivity_period", "2005--2020"), ("only_science", "r/science only"),
               ("only_conspiracy", "r/conspiracy only")]
H1_INDICATORS = [("H1-A", "challenges", "H1-A: challenging the consensus (increase)"), ("H1-A", "supports", "H1-A: supporting the consensus (decrease)"),
                 ("H1-B", "consensus", "H1-B: consensus sources (decrease)"), ("H1-B", "alternative", "H1-B: alternative sources (increase)")]


def h1a_numbers(numbers: Numbers, validation_dir=VALIDATION_DIR, agreement_dir=AGREEMENT_DIR, hypotheses_dir=HYPOTHESES_DIR) -> str:
    """Numbers of H1-A from the outputs of its pipeline (docs/h1a_kroki.md); each missing one is the placeholder macro.

    Returns the status: pending (no stance test yet), gate_failed, awaiting_test (gate passed, no confirmatory
    H1-A rows yet) or tested.
    """
    agreement_path = agreement_dir / "pilot_stance_agreement.csv"
    rows = pd.read_csv(agreement_path).set_index("variable") if agreement_path.exists() else None
    row = rows.loc["consensus_stance"] if rows is not None and "consensus_stance" in rows.index else None
    # After the one stance test an uncoded pilot stays uncoded (amendments of 27.10.2026), so say so.
    uncoded = NOT_CODED if (validation_dir / "stance_test_run.json").exists() else PENDING
    numbers.put("hone a pilot units", count(row["units"]) if row is not None else uncoded)
    numbers.put("hone a pilot alpha", both(row["alpha"], row["alpha_low"], row["alpha_high"]) if row is not None else uncoded)
    numbers.put("hone a pilot kappa", both(row["kappa"], row["kappa_low"], row["kappa_high"]) if row is not None else uncoded)
    numbers.put("hone a pilot agreement", number(row["observed_agreement"]) if row is not None else uncoded)
    for split in ["dev", "test"]:
        metrics_path, run_path = validation_dir / f"stance_{split}_metrics.csv", validation_dir / f"stance_{split}_run.json"
        table = pd.read_csv(metrics_path) if metrics_path.exists() else pd.DataFrame(columns=["metric", "value"])
        # Plan B writes metrics on the reviewed rows (the gate) and on all rows; the preprint reports the gate's.
        table = table[table["rows"].eq("reviewed")] if "rows" in table else table
        values = dict(table[["metric", "value"]].itertuples(index=False))
        run = json.loads(run_path.read_text(encoding="utf-8")) if run_path.exists() else {}
        numbers.put(f"hone a {split} posts", count(run["posts"]) if "posts" in run else PENDING)
        for key, name in [("challenges f", "challenges:f1"), ("kappa", "kappa"), ("macro f", "macro_f1"), ("accuracy", "accuracy")]:
            numbers.put(f"hone a {split} {key}", number(values[name]) if name in values else PENDING)
    run_path = validation_dir / "stance_test_run.json"
    run = json.loads(run_path.read_text(encoding="utf-8")) if run_path.exists() else {}
    passed = run.get("gate", {}).get("passed")
    numbers.put("hone a gate", PENDING if passed is None else ("met" if passed else "not met"))
    thresholds = run.get("thresholds")
    numbers.put("hone a thresholds", PENDING if not thresholds else
                ", ".join(f"{name} {number(thresholds[name])}" for name in ["relevance", "supports", "challenges"]))
    missing = NOT_TESTED if passed is False else PENDING
    trends_path = hypotheses_dir / "confirmatory_trends.csv"
    trends = pd.read_csv(trends_path) if trends_path.exists() else pd.DataFrame(columns=["hypothesis"])
    found = trends[trends["hypothesis"].eq("H1-A")].set_index(["analysis", "outcome"]) if len(trends) else pd.DataFrame()
    labels = {"primary": "", "sensitivity_period": " twenty", "only_science": " science", "only_conspiracy": " conspiracy"}
    for analysis, label in labels.items():
        for outcome in ["challenges", "supports"]:
            key = (analysis, outcome)
            hit = len(found) and key in found.index
            numbers.put(f"hone a {outcome}{label} or",
                        both(found.loc[key, "odds_ratio_per_year"], found.loc[key, "ci_low"], found.loc[key, "ci_high"]) if hit else missing)
            numbers.put(f"hone a {outcome}{label} p", p_value(found.loc[key, "p_one_sided"]) if hit else missing)
    primary = ("primary", "challenges")
    numbers.put("hone a relevant posts", count(found.loc[primary, "units"]) if len(found) and primary in found.index else missing)
    yearly_path = hypotheses_dir / "confirmatory_yearly.csv"
    yearly = pd.read_csv(yearly_path) if yearly_path.exists() else pd.DataFrame(columns=["hypothesis"])
    part = yearly[yearly["hypothesis"].eq("H1-A") & yearly["outcome"].eq("challenges") & yearly["group"].eq("all")] if len(yearly) else yearly
    part = part.set_index("year")["share"] if len(part) else pd.Series(dtype=float)
    numbers.put("hone a challenges share early", percent(part.loc[2005:2009].mean()) if part.loc[2005:2009].notna().any() else missing)
    numbers.put("hone a challenges share late", percent(part.loc[2014:2018].mean()) if part.loc[2014:2018].notna().any() else missing)
    if passed is None:
        status = "pending"
    elif not passed:
        status = "gate_failed"
    else:
        status = "tested" if len(found) else "awaiting_test"
    texts = {"pending": "waiting for stance coding",
             "gate_failed": r"validity criterion not met: H1-A cannot be measured with \kod{stance\_v1}",
             "awaiting_test": "validity criterion met, awaiting the confirmatory test", "tested": "tested"}
    numbers.put("hone a status", texts[status])
    return status


WAITING = r"\resWaiting"
STANCE_SHEETS = ["stance_gold_IS", "stance_gold_JP", "stance_enriched_IS", "stance_enriched_JP"]
QUALITY_GROUPS = {"stance": STANCE_SHEETS, "sources": ["audit_JP"], "errors": ["errors_dev"], "domains": ["domain_review"]}


CONTROL_MEASURES = {"control stance kappa": ("stance", "kappa", 2), "control stance agreement": ("stance", "agreement", None),
                    "control challenges kept": ("stance", "challenges_kept", None),
                    "control audit exact": ("audit", "exact_set", None),
                    "control sources exact": ("sources", "exact_set", None),
                    "control sources pilot exact": ("sources", "exact_set_pilot_consensus", None),
                    "control sources is exact": ("sources_is", "exact_set", None),
                    "control sources gold is exact": ("sources", "exact_set_gold_IS", None),
                    "control sources gold jp exact": ("sources", "exact_set_gold_JP", None)}


def control_numbers(numbers: Numbers, control_dir=ANNOTATIONS_DIR / "control") -> None:
    """Variant A done automatically (amendment of 27.10.2026): stability of the AI labels on a blind second coding
    (stance, audit) and AI against the human source labels (sources). Missing scores give WAITING."""
    path = control_dir / "control_scores.csv"
    scores = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=["task", "measure"])
    for key, (task, measure, digits) in CONTROL_MEASURES.items():
        row = scores[scores["task"].eq(task) & scores["measure"].eq(measure)]
        if row.empty:
            numbers.put(key, WAITING)
        elif digits:
            numbers.put(key, number(row["value"].iloc[0], digits))
        else:
            numbers.put(key, f"{percent(row['value'].iloc[0])} {interval(100 * row['low'].iloc[0], 100 * row['high'].iloc[0], 0)}")
        numbers.put(f"{key} n", count(row["n"].iloc[0]) if len(row) else WAITING)


def plan_c_numbers(numbers: Numbers, agreement_dir=AGREEMENT_DIR, hypotheses_dir=HYPOTHESES_DIR,
                   validation_dir=VALIDATION_DIR, labels_dir=LABELS_DIR) -> None:
    """Plan C (docs/plan_c_reguly.md): enriched sample, share decided by rules, rule precision on the blind controls,
    AI suggestions people changed, stance_v1 precision and recall, and the H1-B audit. Missing inputs give WAITING."""
    sample_path = hypotheses_dir / "stance_enriched_sample.csv"
    sample = pd.read_csv(sample_path, dtype={"unit_id": str}) if sample_path.exists() else pd.DataFrame(columns=["stratum"])
    numbers.put("enriched posts", count(len(sample)) if len(sample) else WAITING)
    for stratum, key in [("topic", "topic"), ("science_terms", "science"), ("rest", "rest")]:
        numbers.put(f"enriched {key}", count(sample["stratum"].eq(stratum).sum()) if len(sample) else WAITING)
    gold_labels, enriched_labels = stance.load_labels("gold", labels_dir), stance.load_labels(stance.ENRICHED_PHASE, labels_dir)
    for split in ["dev", "test"]:
        frame = stance.validation_frame(gold_labels, gold.load_manifest(), split, enriched_labels, sample if len(sample) else None)
        numbers.put(f"stance {split} challenges posts",
                    count(frame[stance.STANCE].eq("challenges").sum()) if len(frame) else WAITING)

    reviews = [pd.read_csv(path) for name in ["gold", stance.ENRICHED_PHASE]
               if (path := agreement_dir / f"{name}_stance_ai_review.csv").exists()]
    review = pd.concat(reviews, ignore_index=True) if reviews else pd.DataFrame(columns=["checked", "changed"])
    checked = review["checked"].sum()
    numbers.put("plan c ai checked", count(checked) if checked else WAITING)
    numbers.put("plan c ai changed", percent(review["changed"].sum() / checked) if checked else WAITING)
    # Who checked the AI suggestions (amendments of 27.10.2026): the person, the AI assistant, or both.
    labels = pd.concat([gold_labels, enriched_labels], ignore_index=True)
    checkers = set(labels.loc[labels["decided_by"].fillna("human").ne("auto"), "verified_by"].dropna()) if "verified_by" in labels else set()
    numbers.put("plan c checked by", {frozenset({"human"}): HUMAN_CHECKER, frozenset({"ai"}): "the AI assistant"}.get(
        frozenset(checkers), f"{HUMAN_CHECKER} and the AI assistant" if checkers else WAITING))

    quality_path = agreement_dir / "llm_quality.csv"
    quality = pd.read_csv(quality_path) if quality_path.exists() else pd.DataFrame(columns=["name"])
    for group, names in QUALITY_GROUPS.items():
        part = quality[quality["name"].isin(names)]
        rows = part["rows"].sum() if len(part) else 0
        controls = part["control_rows"].sum() if len(part) else 0
        kept = (part["control_kept"].fillna(0) * part["control_rows"]).sum() if len(part) else 0
        numbers.put(f"plan c {group} auto share", percent((part["auto_share"] * part["rows"]).sum() / rows) if rows else WAITING)
        numbers.put(f"plan c {group} controls", count(controls) if len(part) else WAITING)
        numbers.put(f"plan c {group} rule precision", f"{count(round(kept))}/{count(controls)}" if controls else WAITING)

    metrics_path, run_path = validation_dir / "stance_test_metrics.csv", validation_dir / "stance_test_run.json"
    table = pd.read_csv(metrics_path) if metrics_path.exists() else pd.DataFrame(columns=["metric", "value"])
    table = table[table["rows"].eq("reviewed")] if "rows" in table else table
    values = dict(table[["metric", "value"]].itertuples(index=False))
    for name, key in [("challenges:precision", "precision"), ("challenges:recall", "recall")]:
        numbers.put(f"hone a test challenges {key}", number(values[name]) if name in values else PENDING)
    run = json.loads(run_path.read_text(encoding="utf-8")) if run_path.exists() else {}
    all_rows = run.get("gate_all_rows", {})
    numbers.put("hone a test all rows challenges f", number(all_rows["challenges_f1"]) if all_rows else PENDING)
    numbers.put("hone a test all rows kappa", number(all_rows["kappa"]) if all_rows else PENDING)
    numbers.put("hone a reviewed posts", count(run["reviewed_posts"]) if "reviewed_posts" in run else PENDING)

    audit_path = hypotheses_dir / "audit_error_rates.csv"
    audit = pd.read_csv(audit_path).set_index(["source", "indicator"]) if audit_path.exists() else pd.DataFrame()
    for indicator in ["consensus", "alternative"]:
        key = ("pooled", indicator)
        found = len(audit) and key in audit.index
        row = audit.loc[key] if found else None
        numbers.put(f"audit {indicator} j", both(row["youden"], row["youden_low"], row["youden_high"]) if found else WAITING)
        numbers.put(f"audit {indicator} sensitivity", number(row["sensitivity"]) if found else WAITING)
        numbers.put(f"audit {indicator} specificity", number(row["specificity"]) if found else WAITING)
        numbers.put(f"audit {indicator} valid", ("valid" if bool(row["valid"]) else "descriptive only") if found else WAITING)
        numbers.put(f"audit {indicator} positives", count(row["positives"]) if found else WAITING)


def h1_table(hypotheses_dir=HYPOTHESES_DIR, h1a_missing: str = PENDING) -> str:
    """H1-A and H1-B trends side by side: one row per indicator, one column per analysis, OR per year [CI] and p.

    `h1a_missing` fills H1-A cells without a result (NOT_TESTED once stance_v1 failed its gate).
    """
    trends_path = hypotheses_dir / "confirmatory_trends.csv"
    trends = pd.read_csv(trends_path).set_index(["hypothesis", "analysis", "outcome"]) if trends_path.exists() else pd.DataFrame()
    rows = []
    for hypothesis, outcome, label in H1_INDICATORS:
        cells = []
        for analysis, _ in H1_ANALYSES:
            key = (hypothesis, analysis, outcome)
            if len(trends) and key in trends.index:
                row = trends.loc[key]
                cells.append(f"{both(row['odds_ratio_per_year'], row['ci_low'], row['ci_high'])}\\newline"
                             f"{{\\scriptsize $p$ = {p_value(row['p_one_sided'])}}}")
            else:
                cells.append(h1a_missing if hypothesis == "H1-A" else PENDING)
        rows.append([label, *cells])
    header = ["Indicator (expected direction)", *(name for _, name in H1_ANALYSES)]
    return tabular(header, rows, "p{3.9cm}" + "p{2.55cm}" * len(H1_ANALYSES), groups=[2])


def stance_table(numbers: Numbers) -> str:
    """Quality of the stance reference (agreement of two people, rule precision, AI suggestions people changed) and
    the dev and test results of stance_v1, with the gate on reviewed rows and on all rows (placeholders until known)."""
    rows = [
        ["two-person agreement (\\kod{pilot2}, without pre-annotations)", numbers["hone a pilot units"], "--", numbers["hone a pilot kappa"],
         f"$\\alpha$ = {numbers['hone a pilot alpha']}"],
        ["reference: rule R14 (blind check)", numbers["plan c stance controls"], "--", "--",
         f"retained {numbers['plan c stance rule precision']}"],
        [f"reference: AI pre-annotation verified by {numbers['plan c checked by']}", numbers["plan c ai checked"], "--", "--",
         f"changed {numbers['plan c ai changed']}"],
        ["\\kod{stance\\_v1}, \\kod{dev} (tuning)", numbers["hone a dev posts"], numbers["hone a dev challenges f"],
         numbers["hone a dev kappa"], f"macro-F1 {numbers['hone a dev macro f']}"],
        ["\\kod{stance\\_v1}, test (single run)", numbers["hone a reviewed posts"], numbers["hone a test challenges f"],
         numbers["hone a test kappa"], f"validity criterion: {numbers['hone a gate']}; precision "
         f"{numbers['hone a test challenges precision']}, recall {numbers['hone a test challenges recall']}"],
        ["test, all rows (sensitivity)", numbers["hone a test posts"], numbers["hone a test all rows challenges f"],
         numbers["hone a test all rows kappa"], "including rule-based labels"],
    ]
    header = ["Measurement", "$n$", "F1 \\kod{challenges}", "$\\kappa$", "Notes"]
    return tabular(header, rows, "p{4.6cm}lllp{4.4cm}", groups=[3])


def figure_stance_confusion(path, validation_dir=VALIDATION_DIR, predictions_dir=PREDICTIONS_DIR, labels_dir=LABELS_DIR,
                            hypotheses_dir=HYPOTHESES_DIR) -> None:
    """Confusion matrix of stance_v1 on the test split (counts, reference by rows); a placeholder before the test."""
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap

    order = ["challenges", "supports", "neutral", "not_applicable"]
    predictions_path = predictions_dir / "stance_v1_test.csv"
    sample_path = hypotheses_dir / "stance_enriched_sample.csv"
    figure, axis = plt.subplots(figsize=(5.2, 3.4), facecolor=SURFACE)
    axis.set_facecolor(SURFACE)
    if not (validation_dir / "stance_test_run.json").exists() or not predictions_path.exists():
        axis.axis("off")
        axis.text(0.5, 0.5, "waiting for the stance_v1 test (07b)", ha="center", va="center", fontsize=10, color=INK_SECONDARY)
        figure.savefig(path, dpi=200, facecolor=SURFACE)
        return
    sample = pd.read_csv(sample_path, dtype={"unit_id": str}) if sample_path.exists() else None
    frame = stance.validation_frame(stance.load_labels("gold", labels_dir), gold.load_manifest(), "test",
                                    stance.load_labels(stance.ENRICHED_PHASE, labels_dir), sample)
    predicted = pd.read_csv(predictions_path, dtype={"unit_id": str}).drop_duplicates("unit_id").set_index("unit_id")[stance.STANCE]
    table = pd.crosstab(frame[stance.STANCE].to_numpy(), predicted.reindex(frame["unit_id"]).to_numpy()).reindex(
        index=order, columns=order, fill_value=0)
    cmap = LinearSegmentedColormap.from_list("ink", [SURFACE, SERIES])
    axis.imshow(table.to_numpy(), cmap=cmap, aspect="auto")
    peak = table.to_numpy().max() or 1
    for (row, column), value in np.ndenumerate(table.to_numpy()):
        axis.text(column, row, str(value), ha="center", va="center", fontsize=9, color=SURFACE if value > peak / 2 else INK)
    labels = ["challenges", "supports", "neutral", "n/a"]
    axis.set_xticks(range(4), labels, fontsize=8, color=INK)
    axis.set_yticks(range(4), labels, fontsize=8, color=INK)
    axis.tick_params(length=0)
    for side in axis.spines.values():
        side.set_visible(False)
    axis.set_xlabel("stance_v1", fontsize=8, color=INK_SECONDARY)
    axis.set_ylabel("reference", fontsize=8, color=INK_SECONDARY)
    axis.set_title(f"stance_v1 on the test split: number of posts (n = {int(table.to_numpy().sum())})", loc="left", fontsize=9, color=INK)
    figure.tight_layout()
    figure.savefig(path, dpi=200, facecolor=SURFACE)


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
    header = ["", "Frame", "Sample: pilot / dev / test", "Gold: dev / test", "Pilot (2 coders)",
              r"$\alpha$ " + code("cites_source"), r"$\alpha$ types (MASI)"]
    return tabular(header, rows, "lrcccrr")


def test_table() -> str:
    """Test-split metrics of the three frozen source instruments (Tab. 2), the English counterpart of test_metrics.tex."""
    table = pd.read_csv(VALIDATION_DIR / "test_metrics.csv")
    specs = [("reddit", "cites_source", "f1", "F1 " + code("cites_source")),
             ("reddit", "cites_source", "kappa", r"$\kappa$ " + code("cites_source")),
             ("reddit", "source_types", "masi", "MASI"), ("reddit", "source_types", "macro_f1", "macro-F1"),
             ("wikipedia", "cites_source", "f1", "F1 " + code("cites_source")),
             ("wikipedia", "edit_about_sources", "f1", "F1 " + code("edit_about_sources")),
             ("wikipedia", "source_types", "masi", "MASI")]
    rows = []
    for platform, variable, name, label in specs:
        cells = []
        for instrument in INSTRUMENTS:
            try:
                row = metric(table, instrument, platform, variable, name)
            except KeyError:
                cells.append("--")
                continue
            shown = name != "kappa"
            cells.append(estimate(row["value"], row["low"] if shown else np.nan, row["high"] if shown else np.nan))
        rows.append([PLATFORMS[platform], label, *cells])
    return tabular(["", "Metric", *INSTRUMENTS.values()], rows, "ll" + "c" * len(INSTRUMENTS), groups=[4])


def h2_table() -> str:
    trends = pd.read_csv(HYPOTHESES_DIR / "confirmatory_trends.csv")
    rows_h2 = trends[trends["hypothesis"].eq("H2")].set_index("analysis")
    robustness = pd.read_csv(HYPOTHESES_DIR / "exploratory_h2_robustness.csv").set_index("analysis")
    permutation = json.loads((HYPOTHESES_DIR / "exploratory_h2_permutation.json").read_text(encoding="utf-8"))
    exact = json.loads((HYPOTHESES_DIR / "exploratory_h2_exact_by_owner.json").read_text(encoding="utf-8"))
    rows = []
    for analysis, label in [("primary", "main test"), ("without_covid19", "without the COVID-19 article"), ("without_2020", "without 2020"),
                            ("classified_only", "classified domains only")]:
        row = rows_h2.loc[analysis]
        rows.append(["preregistered", label, both(row["odds_ratio_per_year"], row["ci_low"], row["ci_high"]),
                     p_value(row["p_one_sided"]), count(row["positives"])])
    rows.append(["exploratory", "permutation of years across revisions", "--", p_value(permutation["p_one_sided"]), "10"])
    for analysis, label in [("Firth, all pages", "Firth logit, all articles"),
                            ("measurement: first addition of each link only", "first addition of each link only"),
                            ("measurement: owner of the post (WHO, GIS posts are institutional)", "by account owner (Firth)")]:
        row = robustness.loc[analysis]
        rows.append(["exploratory", label, both(row["ratio_per_year"], row["ci_low"], row["ci_high"]), p_value(row["p_one_sided"]),
                     count(row["events"])])
    rows.append(["exploratory", "by account owner, exact test", "--", p_value(exact["p_one_sided"]), "2"])
    return tabular(["", "Analysis", "OR/year [95\\% CI]", "one-sided $p$", "Events"], rows, "lllrr", groups=[4])


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
    panels = {"reddit": [("cites_source", "f1", "F1 cites_source"), ("source_types", "masi", "MASI (types)"),
                         ("source_types", "macro_f1", "macro-F1 (types)")],
              "wikipedia": [("cites_source", "f1", "F1 cites_source"), ("edit_about_sources", "f1", "F1 edit_about_sources"),
                            ("source_types", "masi", "MASI (types)")]}
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
        axis.set_title(f"{PLATFORMS[platform]}: test split", loc="left", fontsize=10, color=INK)
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, frameon=False, fontsize=8, labelcolor=INK, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.02))
    figure.supxlabel("metric value (weighted) with 95% bootstrap interval", fontsize=8, color=INK_SECONDARY)
    figure.tight_layout(rect=(0, 0, 1, 0.93))
    figure.savefig(path, dpi=200, facecolor=SURFACE)


def _share_panel(axis, part: pd.DataFrame, title: str, formatter) -> None:
    """Yearly share with its interval, or a placeholder note while the outcome has no results."""
    _axes(axis, "y")
    axis.set_title(title, loc="left", fontsize=9, color=INK)
    if part.empty:
        axis.set_xticks([])
        axis.set_yticks([])
        axis.spines["bottom"].set_visible(False)
        axis.text(0.5, 0.5, "waiting for stance coding and the H1-A test\n(docs/h1a_kroki.md)", ha="center", va="center",
                  fontsize=9, color=INK_SECONDARY, transform=axis.transAxes)
        return
    axis.fill_between(part["year"], part["low"], part["high"], color=SERIES, alpha=0.12, linewidth=0)
    axis.plot(part["year"], part["share"], color=SERIES, linewidth=2)
    axis.plot(part["year"], part["share"], "o", color=SERIES, markersize=4, markeredgecolor=SURFACE, clip_on=False)
    axis.set_ylim(0, max(part["high"].max(), 0.1) * 1.1)
    axis.yaxis.set_major_formatter(formatter)


def _composition_panel(axis, frame: pd.DataFrame, formatter, legend_below: bool = False,
                       title: str = "skład próby H1-B (udział ważony subredditów)") -> None:
    """Weighted subreddit make-up of the H1-B sample per year."""
    weights = frame.groupby(["year", "group"])["weight"].sum().unstack(fill_value=0)
    shares = weights.div(weights.sum(axis=1), axis=0)
    shares = shares[[name for name in ["reddit.com", "science", "skeptic", "conspiracy"] if name in shares]]
    _axes(axis, "y")
    axis.stackplot(shares.index, shares.T.to_numpy(), labels=[f"r/{name}" for name in shares.columns],
                   colors=CATEGORICAL[: shares.shape[1]], edgecolor=SURFACE, linewidth=1.5)
    axis.set_ylim(0, 1)
    axis.set_xlim(shares.index.min(), shares.index.max())
    axis.yaxis.set_major_formatter(formatter)
    axis.set_title(title, loc="left", fontsize=9, color=INK)
    if legend_below:
        axis.legend(frameon=False, fontsize=7, labelcolor=INK, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=4)
    else:
        axis.legend(frameon=False, fontsize=7, labelcolor=INK, loc="upper left", bbox_to_anchor=(1.0, 1.0))


def _percent_formatter(space: str = ""):
    from matplotlib.ticker import FuncFormatter

    return FuncFormatter(lambda value, _: f"{value:.0%}".replace("%", f"{space}%"))


# Panel titles of the H1 figure per language (Polish keeps a space before %, English does not).
H1_FIGURE_LABELS = {
    "pl": {"consensus": "H1-B: źródła konsensusu (wśród postów z powołaniem)",
           "alternative": "H1-B: źródła alternatywne (wśród postów z powołaniem)",
           "challenges": "H1-A: posty podważające konsensus (wśród postów o nauce)",
           "composition": "skład próby H1-B (udział ważony subredditów)", "space": " "},
    "en": {"consensus": "H1-B: consensus sources (among posts citing a source)",
           "alternative": "H1-B: alternative sources (among posts citing a source)",
           "challenges": "H1-A: posts challenging the consensus (among posts about science)",
           "composition": "H1-B sample composition (weighted share of subreddits)", "space": ""},
}


def figure_h1(frame: pd.DataFrame, path, hypotheses_dir=HYPOTHESES_DIR, language: str = "pl") -> None:
    """H1: yearly shares of consensus and alternative sources (H1-B) and the subreddit make-up of the citing posts,
    in one row; the share of posts challenging the consensus (H1-A) comes first, in a 2 x 2 grid, only when H1-A
    was measured (stance_v1 failed its validity gate, so its trend does not exist)."""
    import matplotlib.pyplot as plt

    labels = H1_FIGURE_LABELS[language]
    yearly = pd.read_csv(hypotheses_dir / "confirmatory_yearly.csv")
    yearly = yearly[yearly["group"].eq("all")]
    panels = [("H1-B", "consensus"), ("H1-B", "alternative")]
    if yearly["hypothesis"].eq("H1-A").any():
        panels.insert(0, ("H1-A", "challenges"))
        figure, grid = plt.subplots(2, 2, figsize=(11, 6.2), facecolor=SURFACE)
    else:
        figure, grid = plt.subplots(1, 3, figsize=(13, 3.9), facecolor=SURFACE)
    axes = grid.flatten()
    formatter = _percent_formatter(labels["space"])
    for axis, (hypothesis, outcome) in zip(axes, panels):
        part = yearly[yearly["hypothesis"].eq(hypothesis) & yearly["outcome"].eq(outcome)].sort_values("year")
        _share_panel(axis, part, labels[outcome], formatter)
    _composition_panel(axes[len(panels)], frame, formatter, legend_below=len(panels) == 2, title=labels["composition"])
    figure.tight_layout()
    figure.savefig(path, dpi=200, facecolor=SURFACE)


def figure_h1_slide(frame: pd.DataFrame, path, hypotheses_dir=HYPOTHESES_DIR) -> None:
    """H1-B for a 16:9 slide, without the H1-A panel: consensus and alternative sources per year, each with the
    within-subreddit trend of the confirmatory test, and the subreddit make-up of the sample."""
    import matplotlib.pyplot as plt

    yearly = pd.read_csv(hypotheses_dir / "confirmatory_yearly.csv")
    yearly = yearly[yearly["group"].eq("all") & yearly["hypothesis"].eq("H1-B")]
    trends = pd.read_csv(hypotheses_dir / "confirmatory_trends.csv")
    trends = trends[trends["hypothesis"].eq("H1-B") & trends["analysis"].eq("primary")].set_index("outcome")
    figure, axes = plt.subplots(1, 3, figsize=(13.3, 4.2), facecolor=SURFACE)
    formatter = _percent_formatter(" ")  # the slide stays in Polish
    for axis, (outcome, title) in zip(axes[:2], [("consensus", "źródła konsensusu (wśród postów z powołaniem)"),
                                                 ("alternative", "źródła alternatywne (wśród postów z powołaniem)")]):
        _share_panel(axis, yearly[yearly["outcome"].eq(outcome)].sort_values("year"), title, formatter)
        if outcome in trends.index:
            row = trends.loc[outcome]
            text = (f"trend w subredditach: OR/rok {row['odds_ratio_per_year']:.2f} "
                    f"[{row['ci_low']:.2f}; {row['ci_high']:.2f}], p = {row['p_one_sided']:.2f}").replace(".", ",")
            axis.text(0.0, -0.16, text, transform=axis.transAxes, fontsize=8, color=INK_SECONDARY, va="top")
    _composition_panel(axes[2], frame, formatter, legend_below=True)
    figure.suptitle("H1-B: udział typów źródeł w próbie i jej skład w latach", x=0.01, ha="left", fontsize=11, color=INK)
    figure.tight_layout(rect=(0, 0.02, 1, 0.95))
    figure.savefig(path, dpi=200, facecolor=SURFACE, bbox_inches="tight")


def figure_h2(links: pd.DataFrame, path) -> None:
    """H2: every link counted as alternative, by date and page, coloured by the owner of the account; hollow = re-added."""
    import matplotlib.pyplot as plt

    alternative = links[links["alternative"].eq(1)].copy()
    alternative["when"] = pd.to_datetime(alternative["introduced"], utc=True)
    alternative["owner"] = np.where(alternative["owner_type"].eq("institution"), "institutional account (WHO, GIS)", "alternative source")
    pages = list(dict.fromkeys(alternative.sort_values("page")["page"]))
    figure, axis = plt.subplots(figsize=(9, 2.4), facecolor=SURFACE)
    _axes(axis)
    rng = np.random.default_rng(1)
    for colour, owner in zip([MUTED, CATEGORICAL[1]], ["institutional account (WHO, GIS)", "alternative source"]):
        for first, marker_face in [(True, colour), (False, SURFACE)]:
            part = alternative[alternative["owner"].eq(owner) & alternative["first_addition"].eq(first)]
            if part.empty:
                continue
            y = part["page"].map({page: index for index, page in enumerate(pages)}).to_numpy(float) + rng.uniform(-0.12, 0.12, len(part))
            axis.scatter(part["when"], y, s=48, facecolors=marker_face, edgecolors=colour, linewidths=1.8, zorder=3,
                         label=f"{owner}{'' if first else ', re-addition'}")
    axis.set_yticks(range(len(pages)))
    # Polish article titles keep their name, with an English gloss.
    glosses = {"Globalne ocieplenie": "Globalne ocieplenie\n(Global warming)"}
    axis.set_yticklabels([glosses.get(page, page) for page in pages], fontsize=8, color=INK)
    axis.set_ylim(-0.6, len(pages) - 0.4)
    axis.set_title("H2: all \u2018alternative\u2019 links added to references, 2020\u20132026", loc="left", fontsize=9, color=INK)
    axis.legend(frameon=False, fontsize=7, labelcolor=INK, loc="upper left", bbox_to_anchor=(1.0, 1.05))
    figure.tight_layout()
    figure.savefig(path, dpi=200, facecolor=SURFACE)


# Labels of the agreement figure per language; Polish uses a decimal comma and a space before %.
AGREEMENT_FIGURE_LABELS = {
    "en": {"types": "types (MASI)", "agreement": "agreement", "space": "", "decimal": ".",
           "axis": "Krippendorff's α with 95% bootstrap interval (pilot, 2 coders)"},
    "pl": {"types": "typy (MASI)", "agreement": "zgodność", "space": " ", "decimal": ",",
           "axis": "α Krippendorffa z 95% przedziałem bootstrap (pilotaż, 2 osoby)"},
}


def figure_agreement(table: pd.DataFrame, path, language: str = "en") -> None:
    """Pilot agreement of the two annotators for the headline variables, with Krippendorff's thresholds."""
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter

    labels = AGREEMENT_FIGURE_LABELS[language]
    specs = [("reddit", "cites_source", "Reddit: cites_source"), ("reddit", "source_types", f"Reddit: {labels['types']}"),
             ("wikipedia", "cites_source", "Wikipedia: cites_source"), ("wikipedia", "edit_about_sources", "Wikipedia: edit_about_sources"),
             ("wikipedia", "source_types", f"Wikipedia: {labels['types']}")]
    rows = table.set_index(["platform", "variable"])
    figure, axis = plt.subplots(figsize=(7.5, 2.6), facecolor=SURFACE)
    _axes(axis)
    for threshold in [ALPHA_TENTATIVE, ALPHA_RELIABLE]:
        axis.axvline(threshold, color=INK_SECONDARY, linewidth=1, linestyle=(0, (4, 3)))
        axis.text(threshold, len(specs) - 0.45, f"{threshold:.3g}".replace(".", labels["decimal"]), ha="center", fontsize=7,
                  color=INK_SECONDARY)
    for position, (platform, variable, label) in zip(range(len(specs))[::-1], specs):
        row = rows.loc[(platform, variable)]
        axis.hlines(position, row["alpha_low"], row["alpha_high"], color=SERIES, linewidth=2)
        axis.plot(row["alpha"], position, "o", color=SERIES, markersize=7, markeredgecolor=SURFACE, markeredgewidth=2)
        share = f"{row['observed_agreement']:.0%}".replace("%", f"{labels['space']}%")
        axis.text(1.04, position, f"{labels['agreement']} {share}, n = {int(row['units'])}", va="center", fontsize=7, color=INK_SECONDARY)
    axis.set_yticks(range(len(specs))[::-1])
    axis.set_yticklabels([label for _, _, label in specs], fontsize=8, color=INK)
    axis.set_xlim(-0.3, 1.0)
    axis.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}".replace("-", "−").replace(".", labels["decimal"])))
    axis.set_xlabel(labels["axis"], fontsize=8, color=INK_SECONDARY)
    figure.tight_layout()
    figure.savefig(path, dpi=200, facecolor=SURFACE, bbox_inches="tight")


def main() -> None:
    numbers = Numbers()
    numbers.put("pending", r"\textit{[awaiting H1-A]}")
    numbers.put("waiting", r"\textit{[awaiting data]}")
    coded = data_numbers(numbers)
    agreement_table = agreement_numbers(numbers)
    instrument_numbers(numbers)
    frame = h1_frame()
    h1_numbers(numbers, frame)
    links = h2_links()
    h2_numbers(numbers, links)
    status = h1a_numbers(numbers)
    plan_c_numbers(numbers)
    control_numbers(numbers)
    (REPORT_DIR / "numbers.tex").write_text(macro_file(numbers, "scripts/18_preprint_package.py"), encoding="utf-8")
    (REPORT_DIR / "tables").mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "tables" / "preprint_data.tex").write_text(data_table(coded, agreement_table, numbers), encoding="utf-8")
    (REPORT_DIR / "tables" / "preprint_h2.tex").write_text(h2_table(), encoding="utf-8")
    (REPORT_DIR / "tables" / "preprint_test_metrics.tex").write_text(test_table(), encoding="utf-8")
    (REPORT_DIR / "tables" / "preprint_h1.tex").write_text(
        h1_table(h1a_missing=NOT_TESTED if status == "gate_failed" else PENDING), encoding="utf-8")
    (REPORT_DIR / "tables" / "preprint_stance.tex").write_text(stance_table(numbers), encoding="utf-8")
    figures = REPORT_DIR / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    figure_instruments(figures / "preprint_instruments.png")
    figure_h1(frame, figures / "preprint_h1.png")
    figure_h1(frame, figures / "preprint_h1_en.png", language="en")
    figure_h1_slide(frame, figures / "slide_h1.png")
    figure_h2(links, figures / "preprint_h2.png")
    figure_agreement(agreement_table, figures / "preprint_agreement.png")
    figure_agreement(agreement_table, figures / "preprint_agreement_pl.png", language="pl")
    figure_stance_confusion(figures / "preprint_stance_confusion.png")
    print(f"{len(numbers)} numbers -> {REPORT_DIR / 'numbers.tex'}; tables and figures in {REPORT_DIR}; H1-A: {status}")


if __name__ == "__main__":
    main()
