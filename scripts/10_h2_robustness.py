"""Exploratory robustness analyses of H2 (not preregistered): does the H2 result hold under other models and definitions?

Same data as the confirmatory test (links added to Wikipedia references in the
H2 period). Analyses:
- Firth's penalised logit, which keeps pages without any alternative link and
  copes with rare events, with page fixed effects, pooled, without 2026 (a
  partial year), without 2020 and without the COVID-19 page;
- revision level: whether a revision added any alternative link (Firth), and
  the number of alternative links per revision with the links added as offset
  (Poisson, robust errors);
- other definitions: social media and video only (no blogs); a broad one
  (social_blog, other, unclassified); and the share of established sources
  (scientific, institutional), expected to fall if H2 holds;
- influence: the preregistered model refitted without each alternative link in turn;
- measurement checks, added after reading the ten alternative links: only the
  first addition of each link to a page (reverts re-add the same link), and the
  owner of the post instead of the platform, for the accounts read by hand in
  OFFICIAL_ACCOUNTS (WHO on Periscope, the Polish Chief Sanitary Inspectorate on
  Twitter), whose posts are institutional sources, not alternative ones.
- permutation: the years of the revisions shuffled within each page (2000 times),
  with the preregistered model's year coefficient as the statistic;
- exact conditional test by owner: when the alternative links left by owner are
  all on one page, the share of equally likely sets of that page's links whose
  years sum to at least theirs.
Writes annotations/hypotheses/exploratory_h2_robustness.csv, exploratory_h2_leave_one_out.csv,
exploratory_h2_permutation.json and exploratory_h2_exact_by_owner.json.
"""

import json
import warnings

import numpy as np
import pandas as pd

from digital_media_analysis import hypotheses, robustness, wikipedia_refs
from digital_media_analysis.config_reader import get_hypotheses
from digital_media_analysis.paths import HYPOTHESES_DIR

BLOG_DOMAINS = {"blogspot.com", "wordpress.com", "medium.com", "substack.com", "tumblr.com", "monbiot.com"}
BROAD = ["social_blog", "other", "unclassified"]
ESTABLISHED = ["scientific", "institutional"]
# Accounts on social platforms that belong to institutions, read by hand among
# the alternative links: (domain, account in the first path segment).
OFFICIAL_ACCOUNTS = {("pscp.tv", "who"), ("twitter.com", "gis_gov")}


def account(url: str) -> str:
    """First path segment of a link, lower-case (the account on most platforms)."""
    path = url.split("://", 1)[-1].split("/", 1)
    return path[1].split("/", 1)[0].lower() if len(path) > 1 else ""


def write_json(name: str, payload: dict) -> None:
    (HYPOTHESES_DIR / name).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def row(analysis: str, definition: str, model: str, unit: str, result: dict) -> dict:
    measure = "RR" if "rate_ratio_per_year" in result else "OR"
    return {
        "analysis": analysis, "definition": definition, "model": model, "unit": unit, "measure": measure,
        "ratio_per_year": result.get("rate_ratio_per_year", result.get("odds_ratio_per_year")),
        "ci_low": result["ci_low"], "ci_high": result["ci_high"], "p_one_sided": result["p_one_sided"],
        "units": result["units"], "events": result["positives"], "note": result.get("note", ""),
    }


def main() -> None:
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    settings = get_hypotheses()["h2"]
    start = settings["period"][0]
    links = hypotheses.h2_outcomes(wikipedia_refs.load_added_links(), settings["period"], settings["alternative_categories"])
    links = links.reset_index(drop=True).assign(
        narrow=lambda frame: (frame["alternative"].eq(1) & ~frame["domain"].isin(BLOG_DOMAINS)).astype(int),
        broad=lambda frame: frame["category"].isin(BROAD).astype(int),
        established=lambda frame: frame["category"].isin(ESTABLISHED).astype(int),
    )
    official = [(domain, account(url)) in OFFICIAL_ACCOUNTS for domain, url in zip(links["domain"], links["url"])]
    links["by_owner"] = (links["alternative"].eq(1) & ~pd.Series(official, index=links.index)).astype(int)
    first = links.sort_values("revision_number").drop_duplicates(["page", "url"]).sort_index()
    preregistered = lambda frame, outcome="alternative", direction="increase": hypotheses.trend(  # noqa: E731
        frame, outcome, "page", "revision", direction, start
    )
    rows = [row("preregistered model (for comparison)", "alternative", "ML logit, page FE, clustered by revision", "link", preregistered(links))]

    firth = lambda frame, outcome="alternative", fe="page", direction="increase": robustness.firth_trend(  # noqa: E731
        frame, outcome, fe, direction, start
    )
    rows += [
        row("Firth, all pages", "alternative", "Firth logit, page FE", "link", firth(links)),
        row("Firth, pooled", "alternative", "Firth logit, no FE", "link", firth(links, fe=None)),
        row("Firth, without 2026", "alternative", "Firth logit, page FE", "link", firth(links[links["year"].ne(2026)])),
        row("Firth, without 2020", "alternative", "Firth logit, page FE", "link", firth(links[links["year"].ne(2020)])),
        row("Firth, without COVID-19", "alternative", "Firth logit, page FE", "link", firth(links[links["page"].ne("COVID-19")])),
    ]

    revisions = robustness.revision_counts(links, "alternative")
    rows += [
        row("revision level, any alternative link", "alternative", "Firth logit, page FE", "revision", firth(revisions, outcome="any_event")),
        row("revision level, alternative links per revision", "alternative", "Poisson, offset log(links), page FE, HC1",
            "revision", robustness.poisson_trend(revisions, "page", "increase", start)),
    ]

    rows += [
        row("definition: social media and video only", "narrow", "Firth logit, page FE", "link", firth(links, outcome="narrow")),
        row("definition: broad (social_blog, other, unclassified)", "broad", "ML logit, page FE, clustered by revision", "link",
            preregistered(links, "broad")),
        row("definition: established sources fall", "established", "ML logit, page FE, clustered by revision", "link",
            preregistered(links, "established", "decrease")),
    ]

    rows += [
        row("measurement: first addition of each link only", "alternative", "Firth logit, page FE", "first addition",
            firth(first)),
        row("measurement: owner of the post (WHO, GIS posts are institutional)", "by_owner", "Firth logit, page FE", "link",
            firth(links, outcome="by_owner")),
        row("measurement: owner of the post, first additions only", "by_owner", "Firth logit, page FE", "first addition",
            firth(first, outcome="by_owner")),
    ]

    events = links.index[links["alternative"].eq(1)]
    influence = robustness.leave_one_out(links, "alternative", preregistered, events)
    influence = influence.merge(links[["year", "page", "domain"]], left_on="dropped", right_index=True)
    rows.append({
        "analysis": "influence: preregistered model without one alternative link", "definition": "alternative",
        "model": "ML logit, page FE, clustered by revision", "unit": "link", "measure": "OR",
        "ratio_per_year": influence["odds_ratio_per_year"].median(), "ci_low": influence["odds_ratio_per_year"].min(),
        "ci_high": influence["odds_ratio_per_year"].max(), "p_one_sided": influence["p_one_sided"].max(),
        "units": len(links) - 1, "events": len(events) - 1,
        "note": f"OR: median, min, max over {len(events)} refits; p: largest; p < 0.05 in {int((influence['p_one_sided'] < 0.05).sum())} of {len(events)}",
    })

    table = pd.DataFrame(rows).assign(mode="exploratory")
    HYPOTHESES_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(HYPOTHESES_DIR / "exploratory_h2_robustness.csv", index=False, encoding="utf-8")
    influence.to_csv(HYPOTHESES_DIR / "exploratory_h2_leave_one_out.csv", index=False, encoding="utf-8")

    with_events = links[links.groupby("page")["alternative"].transform("max").eq(1)]
    permutation = robustness.permutation_trend(with_events, lambda frame: preregistered(frame)["beta"], "revision", "page")
    write_json("exploratory_h2_permutation.json", {
        "analysis": "exploratory, not preregistered", "hypothesis": "H2",
        "test": f"permutation of years between revisions within page, {permutation['permutations']} permutations, "
                f"seed {permutation['seed']}, statistic: FE logistic year coefficient on pages with any alternative link",
        "observed_beta": round(permutation["observed_beta"], 3),
        "observed_odds_ratio": round(float(np.exp(permutation["observed_beta"])), 2),
        "p_one_sided": round(permutation["p_one_sided"], 4),
    })
    remaining = links[links["by_owner"].eq(1)]
    if remaining["page"].nunique() == 1:
        page_years = links.loc[links["page"].eq(remaining["page"].iloc[0]), "year"]
        write_json("exploratory_h2_exact_by_owner.json", {
            "analysis": "exploratory, not preregistered", "hypothesis": "H2",
            "definition": "alternative by owner of the post (WHO and GIS posts institutional)",
            "test": f"exact conditional: all remaining alternative links are on {remaining['page'].iloc[0]}; probability that "
                    f"{len(remaining)} links drawn at random from the page's links in the H2 period have a year sum at least as large as observed",
            "links_on_page": len(page_years),
            "observed_years": sorted(int(year) for year in remaining["year"]),
            "p_one_sided": round(robustness.exact_year_sum_test(page_years, remaining["year"]), 4),
        })
    print(f"permutation p = {permutation['p_one_sided']:.4f}")
    for item in table.itertuples(index=False):
        print(f"{item.analysis:<58} {item.measure} {item.ratio_per_year:.2f} [{item.ci_low:.2f}, {item.ci_high:.2f}] "
              f"p={item.p_one_sided:.3f} n={item.units} events={item.events} {item.note}")
    print(f"Written to {HYPOTHESES_DIR}")


if __name__ == "__main__":
    main()
