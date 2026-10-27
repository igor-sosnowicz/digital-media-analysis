"""Results package of the v1-based preprint: number macros, two compact tables and four figures.

Everything comes from the saved result files (and, for the H2 figure, from the
local Wikipedia download the H2 test read); nothing is estimated anew except
the exploratory shift-share split of the H1-B change, computed from the
analysis sample and its labels. Writes:
- report/numbers.tex: one macro per number the text cites (`\\res...`), so the
  prose follows the results; docs/podsumowanie_wynikow.md lists them by section;
- report/tables/preprint_data.tex (data, sample, agreement), preprint_h1.tex
  (H1-A and H1-B trends side by side), preprint_stance.tex (stance agreement and
  stance_v1 on dev and test) and preprint_h2.tex (H2: preregistered test,
  robustness, measurement check); the preprint also uses test_metrics.tex from scripts/13;
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


PENDING = r"\resPending"
# H1-A results that will never exist because stance_v1 failed its validity gate.
NOT_TESTED = r"\textit{nie testowano}"
H1_ANALYSES = [("primary", "główna (2005--2018)"), ("sensitivity_period", "2005--2020"), ("only_science", "tylko r/science"),
               ("only_conspiracy", "tylko r/conspiracy")]
H1_INDICATORS = [("H1-A", "challenges", "H1-A: podważanie konsensusu (wzrost)"), ("H1-A", "supports", "H1-A: wsparcie konsensusu (spadek)"),
                 ("H1-B", "consensus", "H1-B: źródła konsensusu (spadek)"), ("H1-B", "alternative", "H1-B: źródła alternatywne (wzrost)")]


def h1a_numbers(numbers: Numbers, validation_dir=VALIDATION_DIR, agreement_dir=AGREEMENT_DIR, hypotheses_dir=HYPOTHESES_DIR) -> str:
    """Numbers of H1-A from the outputs of its pipeline (docs/h1a_kroki.md); each missing one is the placeholder macro.

    Returns the status: pending (no stance test yet), gate_failed, awaiting_test (gate passed, no confirmatory
    H1-A rows yet) or tested.
    """
    agreement_path = agreement_dir / "pilot_stance_agreement.csv"
    rows = pd.read_csv(agreement_path).set_index("variable") if agreement_path.exists() else None
    row = rows.loc["consensus_stance"] if rows is not None and "consensus_stance" in rows.index else None
    numbers.put("hone a pilot units", count(row["units"]) if row is not None else PENDING)
    numbers.put("hone a pilot alpha", both(row["alpha"], row["alpha_low"], row["alpha_high"]) if row is not None else PENDING)
    numbers.put("hone a pilot kappa", both(row["kappa"], row["kappa_low"], row["kappa_high"]) if row is not None else PENDING)
    numbers.put("hone a pilot agreement", number(row["observed_agreement"]) if row is not None else PENDING)
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
    numbers.put("hone a gate", PENDING if passed is None else ("spełniony" if passed else "niespełniony"))
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
    texts = {"pending": "czeka na kodowanie stanowiska",
             "gate_failed": r"warunek trafności niespełniony: H1-A niemierzalne instrumentem \kod{stance\_v1}",
             "awaiting_test": "warunek trafności spełniony, czeka na test potwierdzający", "tested": "przetestowane"}
    numbers.put("hone a status", texts[status])
    return status


WAITING = r"\resWaiting"
STANCE_SHEETS = ["stance_gold_IS", "stance_gold_JP", "stance_enriched_IS", "stance_enriched_JP"]
QUALITY_GROUPS = {"stance": STANCE_SHEETS, "sources": ["audit_JP"], "errors": ["errors_dev"], "domains": ["domain_review"]}


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
        numbers.put(f"audit {indicator} valid", ("ważny" if bool(row["valid"]) else "tylko opis") if found else WAITING)
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
    header = ["Wskaźnik (oczekiwany kierunek)", *(name for _, name in H1_ANALYSES)]
    return tabular(header, rows, "p{3.9cm}" + "p{2.55cm}" * len(H1_ANALYSES), groups=[2])


def stance_table(numbers: Numbers) -> str:
    """Quality of the stance reference (agreement of two people, rule precision, AI suggestions people changed) and
    the dev and test results of stance_v1, with the gate on reviewed rows and on all rows (placeholders until known)."""
    rows = [
        ["zgodność dwóch osób (\\kod{pilot2}, bez podpowiedzi)", numbers["hone a pilot units"], "--", numbers["hone a pilot kappa"],
         f"$\\alpha$ = {numbers['hone a pilot alpha']}"],
        ["odniesienie: reguła R14 (kontrola na ślepo)", numbers["plan c stance controls"], "--", "--",
         f"zachowane {numbers['plan c stance rule precision']}"],
        ["odniesienie: podpowiedzi AI sprawdzone przez ludzi", numbers["plan c ai checked"], "--", "--",
         f"poprawiono {numbers['plan c ai changed']}"],
        ["\\kod{stance\\_v1}, \\kod{dev} (strojenie)", numbers["hone a dev posts"], numbers["hone a dev challenges f"],
         numbers["hone a dev kappa"], f"macro-F1 {numbers['hone a dev macro f']}"],
        ["\\kod{stance\\_v1}, test (jeden przebieg)", numbers["hone a reviewed posts"], numbers["hone a test challenges f"],
         numbers["hone a test kappa"], f"warunek trafności: {numbers['hone a gate']}; precyzja "
         f"{numbers['hone a test challenges precision']}, czułość {numbers['hone a test challenges recall']}"],
        ["test, wszystkie wiersze (wrażliwość)", numbers["hone a test posts"], numbers["hone a test all rows challenges f"],
         numbers["hone a test all rows kappa"], "z etykietami z reguł"],
    ]
    header = ["Pomiar", "$n$", "F1 \\kod{challenges}", "$\\kappa$", "Uwagi"]
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
        axis.text(0.5, 0.5, "czeka na test stance_v1 (07b)", ha="center", va="center", fontsize=10, color=INK_SECONDARY)
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
    axis.set_ylabel("odniesienie", fontsize=8, color=INK_SECONDARY)
    axis.set_title(f"stance_v1 na teście: liczba postów (n = {int(table.to_numpy().sum())})", loc="left", fontsize=9, color=INK)
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


def _share_panel(axis, part: pd.DataFrame, title: str, formatter) -> None:
    """Yearly share with its interval, or a placeholder note while the outcome has no results."""
    _axes(axis, "y")
    axis.set_title(title, loc="left", fontsize=9, color=INK)
    if part.empty:
        axis.set_xticks([])
        axis.set_yticks([])
        axis.spines["bottom"].set_visible(False)
        axis.text(0.5, 0.5, "czeka na kodowanie stanowiska i test H1-A\n(docs/h1a_kroki.md)", ha="center", va="center",
                  fontsize=9, color=INK_SECONDARY, transform=axis.transAxes)
        return
    axis.fill_between(part["year"], part["low"], part["high"], color=SERIES, alpha=0.12, linewidth=0)
    axis.plot(part["year"], part["share"], color=SERIES, linewidth=2)
    axis.plot(part["year"], part["share"], "o", color=SERIES, markersize=4, markeredgecolor=SURFACE, clip_on=False)
    axis.set_ylim(0, max(part["high"].max(), 0.1) * 1.1)
    axis.yaxis.set_major_formatter(formatter)


def _composition_panel(axis, frame: pd.DataFrame, formatter, legend_below: bool = False) -> None:
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
    axis.set_title("skład próby H1-B (udział ważony subredditów)", loc="left", fontsize=9, color=INK)
    if legend_below:
        axis.legend(frameon=False, fontsize=7, labelcolor=INK, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=4)
    else:
        axis.legend(frameon=False, fontsize=7, labelcolor=INK, loc="upper left", bbox_to_anchor=(1.0, 1.0))


def _percent_formatter():
    from matplotlib.ticker import FuncFormatter

    return FuncFormatter(lambda value, _: f"{value:.0%}".replace("%", " %"))


def figure_h1(frame: pd.DataFrame, path, hypotheses_dir=HYPOTHESES_DIR) -> None:
    """H1: yearly share of posts challenging the consensus (H1-A; a placeholder until its pipeline has run),
    yearly shares of consensus and alternative sources (H1-B) and the subreddit make-up of the citing posts."""
    import matplotlib.pyplot as plt

    yearly = pd.read_csv(hypotheses_dir / "confirmatory_yearly.csv")
    yearly = yearly[yearly["group"].eq("all")]
    figure, grid = plt.subplots(2, 2, figsize=(11, 6.2), facecolor=SURFACE)
    axes = grid.flatten()
    formatter = _percent_formatter()
    panels = [("H1-A", "challenges", "H1-A: posty podważające konsensus (wśród postów o nauce)"),
              ("H1-B", "consensus", "H1-B: źródła konsensusu (wśród postów z powołaniem)"),
              ("H1-B", "alternative", "H1-B: źródła alternatywne (wśród postów z powołaniem)")]
    for axis, (hypothesis, outcome, title) in zip(axes[:3], panels):
        part = yearly[yearly["hypothesis"].eq(hypothesis) & yearly["outcome"].eq(outcome)].sort_values("year")
        _share_panel(axis, part, title, formatter)
    _composition_panel(axes[3], frame, formatter)
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
    formatter = _percent_formatter()
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
    numbers.put("pending", r"\textit{[czeka na H1-A]}")
    numbers.put("waiting", r"\textit{[czeka na dane]}")
    coded = data_numbers(numbers)
    agreement_table = agreement_numbers(numbers)
    instrument_numbers(numbers)
    frame = h1_frame()
    h1_numbers(numbers, frame)
    links = h2_links()
    h2_numbers(numbers, links)
    status = h1a_numbers(numbers)
    plan_c_numbers(numbers)
    (REPORT_DIR / "numbers.tex").write_text(macro_file(numbers, "scripts/18_preprint_package.py"), encoding="utf-8")
    (REPORT_DIR / "tables").mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "tables" / "preprint_data.tex").write_text(data_table(coded, agreement_table, numbers), encoding="utf-8")
    (REPORT_DIR / "tables" / "preprint_h2.tex").write_text(h2_table(), encoding="utf-8")
    (REPORT_DIR / "tables" / "preprint_h1.tex").write_text(
        h1_table(h1a_missing=NOT_TESTED if status == "gate_failed" else PENDING), encoding="utf-8")
    (REPORT_DIR / "tables" / "preprint_stance.tex").write_text(stance_table(numbers), encoding="utf-8")
    figures = REPORT_DIR / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    figure_instruments(figures / "preprint_instruments.png")
    figure_h1(frame, figures / "preprint_h1.png")
    figure_h1_slide(frame, figures / "slide_h1.png")
    figure_h2(links, figures / "preprint_h2.png")
    figure_agreement(agreement_table, figures / "preprint_agreement.png")
    figure_stance_confusion(figures / "preprint_stance_confusion.png")
    print(f"{len(numbers)} numbers -> {REPORT_DIR / 'numbers.tex'}; tables and figures in {REPORT_DIR}; H1-A: {status}")


if __name__ == "__main__":
    main()
