"""List every domain of links added to Wikipedia references in the H2 period, for review by hand.

Writes annotations/hypotheses/domain_review.csv: domain, links, the category from
codebook/domains.yaml, and empty columns `reviewed_category` and `notes` for the
reviewer. Fix disagreements in codebook/domains.yaml (and add unclassified
domains) before the confirmatory run of H2.
"""

from digital_media_analysis import wikipedia_refs
from digital_media_analysis.config_reader import get_hypotheses
from digital_media_analysis.hypotheses import in_years
from digital_media_analysis.paths import HYPOTHESES_DIR


def main() -> None:
    period = get_hypotheses()["h2"]["period"]
    links = in_years(wikipedia_refs.load_added_links().dropna(subset=["year"]), period)
    review = (
        links.groupby(["domain", "category"]).size().rename("links").reset_index()
        .sort_values(["links", "domain"], ascending=[False, True])
        .assign(reviewed_category="", notes="")
    )
    HYPOTHESES_DIR.mkdir(parents=True, exist_ok=True)
    path = HYPOTHESES_DIR / "domain_review.csv"
    review.to_csv(path, index=False, encoding="utf-8")
    unclassified = review[review["category"].eq(wikipedia_refs.UNCLASSIFIED)]
    print(f"{len(review)} domains, {int(review['links'].sum())} links in {period[0]}-{period[1]} -> {path}")
    print(f"unclassified: {len(unclassified)} domains, {int(unclassified['links'].sum())} links")


if __name__ == "__main__":
    main()
