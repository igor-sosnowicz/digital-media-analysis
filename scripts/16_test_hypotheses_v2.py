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

`--confirmatory` is the reported run and needs the committed preregistration v2;
without it the run is exploratory and its files say so.
"""

import argparse
import json
from datetime import UTC, datetime

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from digital_media_analysis import charts, external, hypotheses, inference, multiverse, robustness  # noqa: E402
from digital_media_analysis.config_reader import get_hypotheses_v2  # noqa: E402
from digital_media_analysis.paths import FRAME_LABELS_DIR, HYPOTHESES_V2_DIR  # noqa: E402
from digital_media_analysis.prereg import git, require_committed, uncommitted  # noqa: E402

GENERAL_SUBREDDITS = {"news", "worldnews", "politics", "todayilearned", "askreddit"}
FIGURES = HYPOTHESES_V2_DIR / "figures"


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


def h1(settings: dict, notes: dict) -> tuple[list[dict], pd.DataFrame]:
    stance_path = FRAME_LABELS_DIR / "h1v2_stance_v2.csv"
    test_path = HYPOTHESES_V2_DIR / "h1_instrument_test.json"
    if not (stance_path.exists() and test_path.exists()):
        notes["H1"] = "czeka: stance_v2 musi być nastrojony, zamrożony i oceniony na teście walidacji (skrypt 14 --evaluate)"
        return [], pd.DataFrame()
    test = json.loads(test_path.read_text(encoding="utf-8"))
    period, start = settings["period"], settings["period"][0]
    bound = inference.per_year_bound(settings["sesoi_period_odds_ratio"], period)
    sample = pd.read_csv(HYPOTHESES_V2_DIR / "h1_sample.csv", dtype={"unit_id": str})
    stance = pd.read_csv(stance_path, dtype={"unit_id": str})
    distrust = pd.read_csv(FRAME_LABELS_DIR / "h1v2_distrust_v1.csv", dtype={"unit_id": str})
    frame = sample.merge(stance, on="unit_id").merge(distrust[["unit_id", "distrust"]], on="unit_id")
    frame = frame.assign(year_c=frame["year"] - start, challenges=frame["consensus_stance"].eq("challenges").astype(int),
                         supports=frame["consensus_stance"].eq("supports").astype(int),
                         general=frame["group"].str.lower().isin(GENERAL_SUBREDDITS))
    relevant = frame[frame["consensus_stance"].ne("not_applicable")].reset_index(drop=True)
    main_outcome = "challenges" if test["gate_passed"] else "distrust"
    notes["H1 main outcome"] = main_outcome if test["gate_passed"] else "distrust (stance_v2 nie przeszedł warunku trafności)"
    rows = []
    for analysis, data in [("primary", relevant), ("only posts", relevant[relevant["kind"].eq("post")]),
                           ("only comments", relevant[relevant["kind"].eq("comment")]),
                           ("only science subreddits", relevant[~relevant["general"]]), ("only general subreddits", relevant[relevant["general"]])]:
        for outcome, direction in [(main_outcome, "increase"), ("supports", "decrease")]:
            if outcome == "supports" and main_outcome != "challenges":
                continue
            result = logit_term(data, outcome, "year_c", ["group"], "day")
            rows.append(row("H1", analysis, outcome, "logit, subreddit FE, clustered by day", result, direction, bound))
    if main_outcome == "challenges":
        rows.append(row("H1", "distrust lexicon", "distrust", "logit, subreddit FE, clustered by day",
                        logit_term(relevant, "distrust", "year_c", ["group"], "day"), "increase", bound))
    panel = relevant[relevant["author_id"].isin(relevant.groupby("author_id")["year"].nunique().loc[lambda years: years >= settings["panel_min_years"]].index)]
    rows.append(row("H1", "within author (panel)", main_outcome, "conditional logit by author",
                    inference.within_author_trend(panel, main_outcome, "author_id", start, "increase"), "increase", bound,
                    estimate="odds_ratio_per_year"))
    counts = test["challenges_counts"]["all"]
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


def h2(settings: dict, notes: dict) -> tuple[list[dict], pd.DataFrame]:
    links = pd.read_csv(HYPOTHESES_V2_DIR / "h2_links.csv", dtype={"url": str})
    period, baseline = settings["period"], settings["baseline_period"]
    bound = inference.per_year_bound(settings["sesoi_period_odds_ratio"], period)
    start = period[0]
    links = links.assign(year_c=links["year"] - start, health=links["group"].eq("health").astype(int),
                         alt_upper=(links["alt_owner"].eq(1) | links["uncoded_owner"].eq(1)).astype(int), weight=1.0)
    articles = links[links["ns"].eq(0)]
    in_period = articles[articles["year"].between(*period) & articles["health"].eq(1)]
    main = in_period[in_period["first_addition"]].reset_index(drop=True)
    social = main[main["platform"].fillna("").ne("")]
    notes["H2 uncoded share of social links"] = float(social["uncoded_owner"].mean()) if len(social) else 0.0
    model = "logit, page FE, clustered by revision"
    rows = [row("H2", "primary", "alt_owner", model, logit_term(main, "alt_owner", "year_c", ["article"], "revid", None), "increase", bound)]
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
    return rows, yearly.assign(hypothesis="H2", outcome="alt_owner")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hypotheses", nargs="+", choices=["h1", "h2"], default=["h1", "h2"])
    parser.add_argument("--confirmatory", action="store_true", help="The reported run: the preregistration v2 must be committed.")
    args = parser.parse_args()
    commit = require_committed() if args.confirmatory else git("rev-parse", "HEAD")
    mode = "confirmatory" if args.confirmatory else "exploratory"
    settings = get_hypotheses_v2()
    notes, rows, yearly = {}, [], []
    if "h1" in args.hypotheses:
        found, shares = h1(settings["h1"], notes)
        rows += found
        yearly.append(shares)
    if "h2" in args.hypotheses:
        found, shares = h2(settings["h2"], notes)
        rows += found
        yearly.append(shares)
    table = pd.DataFrame(rows)
    if len(table):
        table["supported"] = table["p_one_sided"] < settings["alpha"]
        table.to_csv(HYPOTHESES_V2_DIR / f"{mode}_trends.csv", index=False, encoding="utf-8")
        primary = table[table["analysis"].eq("primary")]
        charts.forest(table.assign(label=table["hypothesis"] + ": " + table["analysis"] + " (" + table["outcome"] + ")"),
                      "label", "estimate", "ci_low", "ci_high", section="hypothesis", path=FIGURES / f"{mode}_forest.png")
        for item in primary.itertuples(index=False):
            print(f"{item.hypothesis} {item.outcome}: {item.effect} {item.estimate:.3f} [{item.ci_low:.3f}, {item.ci_high:.3f}] "
                  f"p={item.p_one_sided:.4f} TOST p={getattr(item, 'tost_p_tost', np.nan):.4f}")
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
