"""Extended tests of hypotheses H1 and H2 (v2), as preregistered in docs/hipotezy_v2.md.

H1 (Reddit 2005-2018): share of units challenging the consensus of their topic
among units about a consensus topic (stance_v2), expected to rise. Main test:
weighted logit with subreddit fixed effects, errors clustered by day, one-sided,
plus TOST against the smallest effect of interest. Also: supports (expected to
fall), posts and comments apart, science and general subreddits apart, the
distrust lexicon, the within-author trend, the trend corrected for the
instrument's error, the shift-share decomposition and the specification curve;
the survey comparison when data/external/gss_consci.csv exists.

H2 (Wikipedia 2020-2026): share of alternative sources (by account owner)
among first additions of links to references of health articles, expected to
rise. Main test: logit with page fixed effects, errors clustered by revision,
one-sided, plus TOST. Also: the domain and perennial-sources definitions, all
additions, additions not reverted, the bound with uncoded accounts counted as
alternative, talk pages, the rate model, difference in differences against
control articles and the interrupted time series at the break month (with the
2015-2019 baseline), Firth's logit, how long links stay, and the specification curve.

Change 1 (docs/hipotezy_v2.md, docs/plan_poprawy_krok_po_kroku.md): units of v1 (posts of the v1 frames with their
comments, the eight v1 pages) and bulk revisions are left out; the hypothesis ladders add H1-S1 to H1-S3 and H2-S1
to H2-S5; the power gate (scripts/27, annotations/hypotheses_v2/power_gate.json) makes one variant of each family
its primary test, the others secondary or descriptive; Holm adjusts the two primary tests and, within each family,
the secondary ones, and every ladder test gets the v2 verdict (confirmed, refuted: no effect, refuted: opposite
effect, inconclusive). TOST of the H1 stance trend uses the bound flattened by the instrument's error.

`--confirmatory` is the reported run and needs the committed preregistration v2 and the committed power gate;
without it the run is exploratory and its files say so.
"""

import argparse
import json
from datetime import UTC, datetime

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from digital_media_analysis import charts, external, hypotheses, inference, ladders, multiverse, robustness, wikipedia_refs  # noqa: E402
from digital_media_analysis.config_reader import get_hypotheses_v2, get_wikipedia_pages  # noqa: E402
from digital_media_analysis.datasets import page_title  # noqa: E402
from digital_media_analysis.owners import UNCODED  # noqa: E402
from digital_media_analysis.paths import FRAME_LABELS_DIR, HYPOTHESES_V2_DIR, PROJECT_ROOT  # noqa: E402
from digital_media_analysis.prereg import git, require_committed, uncommitted  # noqa: E402

GENERAL_SUBREDDITS = {"news", "worldnews", "politics", "todayilearned", "askreddit"}
FIGURES = HYPOTHESES_V2_DIR / "figures"
GATE_PATH = HYPOTHESES_V2_DIR / "power_gate.json"


def row(hypothesis: str, analysis: str, outcome: str, model: str, result: dict, direction: str, bound: float | None,
        estimate: str = "odds_ratio", effect: str = "OR") -> dict:
    beta, se = result.get("beta", np.nan), result.get("se", np.nan)
    z = beta / se if se and np.isfinite(se) and se > 0 else np.nan
    record = {"hypothesis": hypothesis, "analysis": analysis, "outcome": outcome, "model": model, "effect": effect,
              "estimate": result.get(estimate, np.exp(beta) if np.isfinite(beta) else np.nan),
              "ci_low": result.get("ci_low", np.nan), "ci_high": result.get("ci_high", np.nan),
              "p_one_sided": result.get("p_one_sided", inference.one_sided(z, direction) if np.isfinite(z) else np.nan),
              "units": result.get("units", np.nan), "events": result.get("positives", result.get("events", np.nan)),
              "direction": direction, "note": result.get("note", "")}
    if bound and np.isfinite(beta) and np.isfinite(se):
        record.update({f"tost_{key}": value for key, value in inference.tost(beta, se, bound).items()})
    return record


def logit_term(frame: pd.DataFrame, outcome: str, term: str, fixed_effects: list[str], cluster: str, weight: str | None = "weight") -> dict:
    table = inference.fe_logit(frame, outcome, [term], fixed_effects, cluster, weight)
    return table.iloc[0].to_dict()


def h1_sample(rules: dict) -> pd.DataFrame:
    """The H1 analysis sample without the posts of the v1 frames and their comments (change 1)."""
    sample = pd.read_csv(HYPOTHESES_V2_DIR / "h1_sample.csv", dtype={"unit_id": str, "post_id": str})
    if rules["exclude_v1_units"] and "post_id" in sample:
        sample = ladders.without_v1_posts(sample, ladders.v1_post_ids(PROJECT_ROOT / folder for folder in rules["v1_reddit_frames"]))
    return sample


def h1(settings: dict, notes: dict, rules: dict) -> tuple[list[dict], pd.DataFrame]:
    stance_path = FRAME_LABELS_DIR / "h1v2_stance_v2.csv"
    test_path = HYPOTHESES_V2_DIR / "h1_instrument_test.json"
    if not (stance_path.exists() and test_path.exists()):
        notes["H1"] = "czeka: stance_v2 musi być nastrojony, zamrożony i oceniony na teście walidacji (skrypt 14 --evaluate)"
        return [], pd.DataFrame()
    test = json.loads(test_path.read_text(encoding="utf-8"))
    period, start = settings["period"], settings["period"][0]
    bound = inference.per_year_bound(settings["sesoi_period_odds_ratio"], period)
    sample = h1_sample(rules)
    stance = pd.read_csv(stance_path, dtype={"unit_id": str})
    distrust = pd.read_csv(FRAME_LABELS_DIR / "h1v2_distrust_v1.csv", dtype={"unit_id": str})
    frame = sample.merge(stance, on="unit_id").merge(distrust[["unit_id", "distrust"]], on="unit_id")
    frame = frame.assign(year_c=frame["year"] - start, challenges=frame["consensus_stance"].eq("challenges").astype(int),
                         supports=frame["consensus_stance"].eq("supports").astype(int),
                         general=frame["group"].str.lower().isin(GENERAL_SUBREDDITS))
    relevant = frame[frame["consensus_stance"].ne("not_applicable")].reset_index(drop=True)
    main_outcome = "challenges" if test["gate_passed"] else "distrust"
    notes["H1 main outcome"] = main_outcome if test["gate_passed"] else "distrust (stance_v2 nie przeszedł warunku trafności)"
    counts = test["challenges_counts"]["all"]
    # Change 1: TOST of the primary stance trend against the bound flattened by the instrument's error.
    primary_bound = bound
    if main_outcome == "challenges":
        sensitivity = counts["tp"] / max(counts["tp"] + counts["fn"], 1)
        specificity = counts["tn"] / max(counts["tn"] + counts["fp"], 1)
        primary_bound = ladders.attenuated_bound(bound, float(relevant["challenges"].mean()), sensitivity, specificity)
        notes["H1 TOST bound per year (flattened by instrument error)"] = primary_bound
    rows = []
    for analysis, data in [("primary", relevant), ("only posts", relevant[relevant["kind"].eq("post")]),
                           ("only comments", relevant[relevant["kind"].eq("comment")]),
                           ("only science subreddits", relevant[~relevant["general"]]), ("only general subreddits", relevant[relevant["general"]])]:
        for outcome, direction in [(main_outcome, "increase"), ("supports", "decrease")]:
            if outcome == "supports" and main_outcome != "challenges":
                continue
            result = logit_term(data, outcome, "year_c", ["group"], "day")
            tost_bound = primary_bound if analysis == "primary" and outcome == main_outcome else bound
            rows.append(row("H1", analysis, outcome, "logit, subreddit FE, clustered by day", result, direction, tost_bound))
    if main_outcome == "challenges":
        rows.append(row("H1", "distrust lexicon", "distrust", "logit, subreddit FE, clustered by day",
                        logit_term(relevant, "distrust", "year_c", ["group"], "day"), "increase", bound))
    panel = relevant[relevant["author_id"].isin(relevant.groupby("author_id")["year"].nunique().loc[lambda years: years >= settings["panel_min_years"]].index)]
    rows.append(row("H1", "within author (panel)", main_outcome, "conditional logit by author",
                    inference.within_author_trend(panel, main_outcome, "author_id", start, "increase"), "increase", bound,
                    estimate="odds_ratio_per_year"))
    if main_outcome == "challenges":
        draws = inference.error_rate_draws(counts["tp"], counts["fn"], counts["tn"], counts["fp"], 100, 20261025)
        corrected = inference.corrected_trend(relevant.assign(year=relevant["year"]), "challenges", "group", "day", start, draws)
        rows.append(row("H1", "corrected for instrument error", "challenges", "misclassification-adjusted logit",
                        corrected, "increase", bound, estimate="odds_ratio_per_year"))
    decomposition = inference.shift_share(relevant, main_outcome, "group", [period[0], period[0] + 4], [period[1] - 4, period[1]])
    notes["H1 shift-share"] = decomposition

    def fit(choice: dict) -> dict:
        data = relevant if choice["kind"] == "all" else relevant[relevant["kind"].eq(choice["kind"])]
        result = logit_term(data, choice["outcome"], "year_c", [] if choice["fixed effect"] == "none" else ["group"], "day",
                            None if choice["weights"] == "equal" else "weight")
        return {"estimate": result["odds_ratio"], "ci_low": result["ci_low"], "ci_high": result["ci_high"],
                "p_one_sided": inference.one_sided(result["z"], "increase")}

    curve = multiverse.run({"outcome": ["challenges", "distrust"], "kind": ["all", "post", "comment"],
                            "weights": ["design", "equal"], "fixed effect": ["subreddit", "none"]}, fit)
    curve.to_csv(HYPOTHESES_V2_DIR / "h1_specifications.csv", index=False, encoding="utf-8")
    notes["H1 specifications"] = multiverse.summary(curve)
    yearly = hypotheses.yearly_shares(relevant, main_outcome, strata=["group", "year"], samples=500)
    by_group = hypotheses.yearly_shares(relevant, main_outcome, by=["group"], strata=["group", "year"], samples=200)
    FIGURES.mkdir(parents=True, exist_ok=True)
    charts.yearly_panels(by_group, "group", path=FIGURES / "h1_yearly_by_subreddit.png")
    charts.composition(relevant.groupby(["year", "group"], as_index=False)["weight"].sum(), "year", "group", "weight",
                       path=FIGURES / "h1_composition.png")
    charts.decomposition(pd.DataFrame([{"outcome": main_outcome, **decomposition}]), "outcome", path=FIGURES / "h1_decomposition.png")
    charts.specification_curve(curve, ["outcome", "kind", "weights", "fixed effect"], path=FIGURES / "h1_specifications.png")
    if main_outcome == "challenges":
        sensitivity = counts["tp"] / max(counts["tp"] + counts["fn"], 1)
        specificity = counts["tn"] / max(counts["tn"] + counts["fp"], 1)
        corrected_yearly = yearly.assign(share=yearly["share"].map(lambda p: hypotheses.rogan_gladen(p, sensitivity, specificity)),
                                         low=np.nan, high=np.nan)
        both = pd.concat([yearly.assign(series="instrument"), corrected_yearly.assign(series="skorygowany")], ignore_index=True)
        charts.lines(both, "year", "series", "share", ylabel="udział challenges", path=FIGURES / "h1_naive_vs_corrected.png")
    if external.GSS_PATH.exists():
        survey = external.load_gss()
        notes["H1 external (GSS great deal)"] = external.compare(yearly, survey, "share", "great_deal")
        charts.labelled_scatter(yearly.merge(survey, on="year"), "great_deal", "share", "year",
                                "GSS: duże zaufanie do środowiska naukowego", f"Reddit: udział {main_outcome}",
                                path=FIGURES / "h1_external.png")
    return rows, yearly.assign(hypothesis="H1", outcome=main_outcome)


def h2(settings: dict, notes: dict, rules: dict) -> tuple[list[dict], pd.DataFrame]:
    links = pd.read_csv(HYPOTHESES_V2_DIR / "h2_links.csv", dtype={"url": str})
    period, baseline = settings["period"], settings["baseline_period"]
    bound = inference.per_year_bound(settings["sesoi_period_odds_ratio"], period)
    start = period[0]
    links = links.assign(year_c=links["year"] - start, health=links["group"].eq("health").astype(int),
                         alt_upper=(links["alt_owner"].eq(1) | links["uncoded_owner"].eq(1)).astype(int), weight=1.0)
    articles = links[links["ns"].eq(0)]
    # Change 1: bulk revisions and the v1 pages leave the analyses; the main test with bulk revisions is reported apart.
    with_bulk = articles[articles["year"].between(*period) & articles["health"].eq(1) & articles["first_addition"]].reset_index(drop=True)
    articles = ladders.without_bulk(articles, int(rules["h2"]["bulk_revision_links"]))
    if rules["exclude_v1_units"]:
        articles = ladders.without_pages(articles, [page_title(url) for url in get_wikipedia_pages()])
    in_period = articles[articles["year"].between(*period) & articles["health"].eq(1)]
    main = in_period[in_period["first_addition"]].reset_index(drop=True)
    social = main[main["platform"].fillna("").ne("")]
    notes["H2 uncoded share of social links"] = float(social["uncoded_owner"].mean()) if len(social) else 0.0
    model = "logit, page FE, clustered by revision"
    rows = [row("H2", "primary", "alt_owner", model, logit_term(main, "alt_owner", "year_c", ["article"], "revid", None), "increase", bound),
            row("H2", "with bulk revisions", "alt_owner", model, logit_term(with_bulk, "alt_owner", "year_c", ["article"], "revid", None),
                "increase", bound)]
    for analysis, data, outcome in [
        ("definition: domain category", main, "alt_domain"), ("definition: perennial sources", main, "alt_rsp"),
        ("all additions", in_period, "alt_owner"), ("first additions not reverted", main[~main["reverted_edit"]], "alt_owner"),
        ("uncoded accounts as alternative (upper bound)", main, "alt_upper"),
        ("talk pages", links[links["ns"].eq(1) & links["year"].between(*period) & links["health"].eq(1) & links["first_addition"]], "alt_owner"),
    ]:
        rows.append(row("H2", analysis, outcome, model, logit_term(data, outcome, "year_c", ["article"], "revid", None), "increase", bound))
    rows.append(row("H2", "Firth, pooled", "alt_owner", "Firth logit, no FE",
                    robustness.firth_trend(main.assign(year=main["year"]), "alt_owner", None, "increase", start), "increase", bound,
                    estimate="odds_ratio_per_year"))
    panel = main.groupby(["article", "month", "year"], as_index=False).agg(events=("alt_owner", "sum"), links=("url", "size"))
    panel = panel.assign(year_c=panel["year"] - start)
    rows.append(row("H2", "rate per page-month", "alt_owner", "negative binomial, offset log(links), page FE",
                    inference.rate_trend(panel, "events", "links", ["year_c"], "article", "article", "increase", "year_c"),
                    "increase", None, estimate="rate_ratio", effect="RR"))
    window = articles[articles["year"].between(baseline[0], period[1]) & articles["first_addition"]].reset_index(drop=True)
    window = window.assign(post=(window["month"] >= settings["break_month"]).astype(int))
    window = window.assign(health_post=window["health"] * window["post"])
    rows.append(row("H2", "difference in differences (health vs control, after the break)", "alt_owner",
                    "logit, page and year FE, clustered by revision",
                    logit_term(window, "alt_owner", "health_post", ["article", "year"], "revid", None), "increase", None))
    health = window[window["health"].eq(1)].copy()
    months = pd.to_datetime(health["month"] + "-01")
    break_time = pd.Timestamp(settings["break_month"] + "-01")
    health["t"] = (months - pd.Timestamp(f"{baseline[0]}-01-01")).dt.days / 365.25
    health["t_after"] = ((months - break_time).dt.days / 365.25).clip(lower=0)
    its = inference.fe_logit(health, "alt_owner", ["t", "post", "t_after"], ["article"], "revid", None)
    for term, label in [("post", "interrupted time series: level change at the break"), ("t_after", "interrupted time series: slope change after the break")]:
        rows.append(row("H2", label, "alt_owner", "segmented logit, page FE", its[its["term"].eq(term)].iloc[0].to_dict(), "increase", None))
    lasting = main.assign(type=np.where(main["alt_owner"].eq(1), "alternatywne", "pozostałe"))
    curves, comparison = inference.survival(lasting, "days_present", "censored", "type")
    notes["H2 survival"] = comparison

    def fit(choice: dict) -> dict:
        data = links[links["ns"].eq(choice["namespace"]) & links["year"].between(*period) & links["health"].eq(1)]
        if choice["unit"] != "all additions":
            data = data[data["first_addition"]]
        if choice["unit"] == "first, not reverted":
            data = data[~data["reverted_edit"]]
        if choice["model"] == "Firth pooled":
            result = robustness.firth_trend(data, choice["definition"], None, "increase", start)
            return {"estimate": result["odds_ratio_per_year"], "ci_low": result["ci_low"], "ci_high": result["ci_high"],
                    "p_one_sided": result["p_one_sided"]}
        result = logit_term(data, choice["definition"], "year_c", ["article"], "revid", None)
        return {"estimate": result["odds_ratio"], "ci_low": result["ci_low"], "ci_high": result["ci_high"],
                "p_one_sided": inference.one_sided(result["z"], "increase")}

    curve = multiverse.run({"definition": ["alt_owner", "alt_domain", "alt_rsp"], "unit": ["all additions", "first additions", "first, not reverted"],
                            "namespace": [0, 1], "model": ["logit page FE", "Firth pooled"]}, fit)
    curve.to_csv(HYPOTHESES_V2_DIR / "h2_specifications.csv", index=False, encoding="utf-8")
    notes["H2 specifications"] = multiverse.summary(curve)
    yearly = hypotheses.yearly_shares(window, "alt_owner", by=["group"], strata=["year"], samples=500)
    FIGURES.mkdir(parents=True, exist_ok=True)
    marker = int(settings["break_month"][:4]) + (int(settings["break_month"][5:]) - 1) / 12
    charts.lines(yearly, "year", "group", "share", "low", "high", marker=marker, marker_label="przerwa",
                 ylabel="udział linków alternatywnych", path=FIGURES / "h2_health_vs_control.png")
    counts = window[window["health"].eq(1)].groupby("year", as_index=False).size()
    charts.columns(counts, "year", "size", "pierwsze dodania linków (artykuły o zdrowiu)", marker=marker, marker_label="przerwa",
                   path=FIGURES / "h2_additions_per_year.png")
    owners_by_year = social.assign(owner_type=social["owner_type"].replace("", "brak konta")).groupby(["year", "owner_type"], as_index=False).size()
    if len(owners_by_year):
        charts.stacked_bars(owners_by_year, "year", "owner_type", "size", path=FIGURES / "h2_owner_types.png")
    alternative = main[main["alt_owner"].eq(1)]
    if len(alternative):
        charts.event_timeline(alternative, "timestamp", "title", "owner_type", path=FIGURES / "h2_alternative_timeline.png")
    if len(curves):
        charts.survival_curves(curves, "type", path=FIGURES / "h2_survival.png")
    top = main["title"].value_counts().index[:30]
    heat = main[main["title"].isin(top)].pivot_table(index="title", columns="year", values="alt_owner", aggfunc="mean")
    if len(heat):
        charts.heatmap(heat, "udział alternatywnych", path=FIGURES / "h2_heatmap.png")
    charts.specification_curve(curve, ["definition", "unit", "namespace", "model"], path=FIGURES / "h2_specifications.png")
    rows += h2_ladder(articles, settings, rules)
    return rows, yearly.assign(hypothesis="H2", outcome="alt_owner")


def h1_ladder(settings: dict, rules: dict, notes: dict) -> list[dict]:
    """H1-S1 and H1-S2 (gliner_v1 sources of the sample units) and H1-S3 (participation, no labels) of change 1."""
    if not (HYPOTHESES_V2_DIR / "h1_sample.csv").exists():
        return []
    start = settings["period"][0]
    bound = inference.per_year_bound(settings["sesoi_period_odds_ratio"], settings["period"])
    sample = h1_sample(rules).assign(year_c=lambda frame: frame["year"] - start)
    questioning = {name.lower() for name in rules["h1"]["questioning_subreddits"]}
    sample["questioning"] = sample["group"].str.lower().isin(questioning).astype(int)
    rows = [row("H1", "H1-S3: share of units in questioning communities", "questioning", "weighted logit, no FE, clustered by day",
                logit_term(sample, "questioning", "year_c", [], "day"), "increase", bound) | {"variant": "H1-S3"}]
    sources_path = FRAME_LABELS_DIR / "h1v2_gliner_v1.csv"
    if not sources_path.exists():
        notes["H1-S1, H1-S2"] = "czeka: etykiety źródeł gliner_v1 (skrypt 14 --sources)"
        return rows
    labels = pd.read_csv(sources_path, dtype={"unit_id": str})
    citing = sample.merge(labels[labels["cites_source"].astype(int).eq(1)][["unit_id", "source_types"]], on="unit_id")
    citing = citing.assign(alternative=hypotheses.has_any(citing["source_types"], rules["h1"]["alternative_sources"]))
    errors = pd.read_csv(PROJECT_ROOT / "annotations" / "hypotheses" / "audit_error_rates.csv")
    errors = errors[errors["source"].eq("pooled") & errors["indicator"].eq("alternative")].iloc[0]
    # TOST against the bound flattened by gliner_v1's error on alternative sources (v1 audit).
    flattened = ladders.attenuated_bound(bound, float(citing["alternative"].mean()), errors["sensitivity"], errors["specificity"])
    for variant, analysis, effects in (("H1-S1", "H1-S1: alternative sources within communities", ["group"]),
                                       ("H1-S2", "H1-S2: alternative sources in the whole discussion", [])):
        model = "weighted logit, " + ("subreddit FE" if effects else "no FE") + ", clustered by day"
        rows.append(row("H1", analysis, "alternative", model, logit_term(citing, "alternative", "year_c", effects, "day"), "increase",
                        flattened) | {"variant": variant})
    return rows


def h2_ladder(articles: pd.DataFrame, settings: dict, rules: dict) -> list[dict]:
    """H2-S1 to H2-S5 of change 1 on first additions to articles without v1 pages and bulk revisions."""
    period, extra = settings["period"], rules["h2"]
    bound = inference.per_year_bound(settings["sesoi_period_odds_ratio"], period)
    first = articles[articles["year"].between(*period) & articles["first_addition"]].reset_index(drop=True)
    classified = first[first["category"].ne(wikipedia_refs.UNCLASSIFIED)]
    classified = classified.assign(non_specialist=classified["category"].isin(extra["non_specialist_categories"]).astype(int))
    health = classified[classified["health"].eq(1)]
    rows = [row("H2", "H2-S1: non-specialist sources", "non_specialist", "logit, page FE, clustered by revision",
                logit_term(health, "non_specialist", "year_c", ["article"], "revid", None), "increase", bound) | {"variant": "H2-S1"},
            row("H2", "H2-S2: health against control articles", "non_specialist", "logit, no FE, clustered by page",
                logit_term(classified, "non_specialist", "health", [], "article", None), "increase", extra["group_sesoi_odds_ratio"])
            | {"variant": "H2-S2"}]
    lasting = health.assign(type=np.where(health["non_specialist"].eq(1), "nieeksperckie", "eksperckie"))
    _, comparison = inference.survival(lasting, "days_present", "censored", "type")
    if {"hazard_ratio", "ci_low", "ci_high"} <= set(comparison):
        se = (np.log(comparison["ci_high"]) - np.log(comparison["ci_low"])) / (2 * 1.959964)
        result = {"beta": np.log(comparison["hazard_ratio"]), "se": se, "hazard_ratio": comparison["hazard_ratio"],
                  "ci_low": comparison["ci_low"], "ci_high": comparison["ci_high"], "units": len(lasting),
                  "events": int((~lasting["censored"].astype(bool)).sum())}
        rows.append(row("H2", "H2-S3: removal of non-specialist against specialist links", "removal", "Cox, time to removal", result,
                        "increase", extra["survival_hazard_ratio"], estimate="hazard_ratio", effect="HR") | {"variant": "H2-S3"})
    main = first[first["health"].eq(1)]
    below = ladders.share_below(main["alt_owner"], main["article"], extra["marginal_share"])
    rows.append({"hypothesis": "H2", "analysis": f"H2-S4: alternative sources below {extra['marginal_share']:.0%} of first additions",
                 "outcome": "alt_owner", "model": "share, page-clustered error", "effect": "share", "estimate": below["estimate"],
                 "ci_low": np.nan, "ci_high": below["ci_high"], "p_one_sided": below["p_one_sided"], "units": below["units"],
                 "events": below["events"], "direction": "below", "note": "", "variant": "H2-S4"})
    owned = main[main["alt_domain"].eq(1) & ~main["owner_type"].fillna("").isin(["", UNCODED])]
    above = ladders.share_above(int(owned["owner_type"].eq(ladders.INSTITUTION).sum()), len(owned), extra["institution_null_share"])
    rows.append({"hypothesis": "H2", "analysis": "H2-S5: institutions' accounts among alternative links by domain", "outcome": "institution",
                 "model": "exact binomial", "effect": "share", "estimate": above["estimate"], "ci_low": above.get("ci_low", np.nan),
                 "ci_high": above.get("ci_high", np.nan), "p_one_sided": above["p_one_sided"], "units": above["units"],
                 "events": above["events"], "direction": "above", "note": "", "variant": "H2-S5"})
    return rows


def verdict(item: pd.Series, alpha: float) -> str:
    """The v2 decision rule on Holm-adjusted p-values (primary and secondary) or raw ones (descriptive, marked)."""
    if item["role"] == "analysis":
        return ""
    suffix = "" if item["role"] == "descriptive" else "_holm"
    if item.get(f"p_one_sided{suffix}", np.nan) < alpha:
        found = "potwierdzona"
    elif item.get(f"tost_p_tost{suffix}", np.nan) < alpha:
        found = "obalona: brak efektu"
    elif item.get(f"p_opposite{suffix}", np.nan) < alpha:
        found = "obalona: efekt przeciwny"
    else:
        found = "nierozstrzygnięta"
    return found + (" (opisowo)" if item["role"] == "descriptive" else "")


def decide(table: pd.DataFrame, roles: dict[str, str], alpha: float) -> pd.DataFrame:
    """Variant and role of every row, Holm across the primary tests and within each family's secondary tests, verdicts."""
    table = table.copy()
    if "variant" not in table:
        table["variant"] = np.nan
    table.loc[table["analysis"].eq("primary"), "variant"] = table["hypothesis"]
    table["role"] = table["variant"].map(lambda variant: roles.get(variant, "descriptive") if isinstance(variant, str) else "analysis")
    if "tost_p_tost" not in table:
        table["tost_p_tost"] = np.nan
    table["p_opposite"] = np.where(table["effect"].isin(["OR", "HR", "RR"]), 1 - table["p_one_sided"], np.nan)
    families = [table.index[table["role"].eq("primary")]]
    families += [table.index[table["role"].eq("secondary") & table["hypothesis"].eq(name)] for name in ("H1", "H2")]
    for column in ("p_one_sided", "tost_p_tost", "p_opposite"):
        table[f"{column}_holm"] = np.nan
        for index in families:
            if len(index):
                table.loc[index, f"{column}_holm"] = pd.Series(ladders.holm(table.loc[index, column].to_dict()))
    table["verdict"] = table.apply(verdict, axis=1, alpha=alpha)
    return table


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hypotheses", nargs="+", choices=["h1", "h2"], default=["h1", "h2"])
    parser.add_argument("--confirmatory", action="store_true", help="The reported run: the preregistration v2 must be committed.")
    args = parser.parse_args()
    commit = require_committed() if args.confirmatory else git("rev-parse", "HEAD")
    gate_file = GATE_PATH.relative_to(PROJECT_ROOT).as_posix()
    if args.confirmatory and (not GATE_PATH.exists() or uncommitted([gate_file])):
        raise SystemExit(f"Commit {gate_file} (scripts/27_power_gate.py) before the confirmatory run.")
    roles = ladders.roles(json.loads(GATE_PATH.read_text(encoding="utf-8"))["decision"]) if GATE_PATH.exists() else {}
    mode = "confirmatory" if args.confirmatory else "exploratory"
    settings = get_hypotheses_v2()
    notes, rows, yearly = {}, [], []
    if "h1" in args.hypotheses:
        found, shares = h1(settings["h1"], notes, settings["ladders"])
        rows += found + h1_ladder(settings["h1"], settings["ladders"], notes)
        yearly.append(shares)
    if "h2" in args.hypotheses:
        found, shares = h2(settings["h2"], notes, settings["ladders"])
        rows += found
        yearly.append(shares)
    table = pd.DataFrame(rows)
    if len(table):
        table["supported"] = table["p_one_sided"] < settings["alpha"]
        table = decide(table, roles, settings["alpha"])
        table.to_csv(HYPOTHESES_V2_DIR / f"{mode}_trends.csv", index=False, encoding="utf-8")
        charts.forest(table.assign(label=table["hypothesis"] + ": " + table["analysis"] + " (" + table["outcome"] + ")"),
                      "label", "estimate", "ci_low", "ci_high", section="hypothesis", path=FIGURES / f"{mode}_forest.png")
        for item in table[table["role"].ne("analysis")].itertuples(index=False):
            print(f"{item.variant} [{item.role}] {item.outcome}: {item.effect} {item.estimate:.3f} p={item.p_one_sided:.4f} "
                  f"TOST p={item.tost_p_tost:.4f} -> {item.verdict}")
    if any(len(part) for part in yearly):
        pd.concat(yearly, ignore_index=True).to_csv(HYPOTHESES_V2_DIR / f"{mode}_yearly.csv", index=False, encoding="utf-8")
    (HYPOTHESES_V2_DIR / f"{mode}_run.json").write_text(json.dumps({
        "mode": mode, "created_utc": datetime.now(UTC).isoformat(timespec="seconds"), "commit": commit,
        "uncommitted_preregistration": bool(uncommitted()), "settings": settings, "notes": notes,
    }, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    for key, value in notes.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
