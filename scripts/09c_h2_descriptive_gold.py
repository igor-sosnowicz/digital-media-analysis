"""Preregistered descriptive indicator of H2 (docs/hipotezy.md): the yearly share of Wikipedia edit summaries in the
manual gold that cite an alternative, unknown or personal source.

Descriptive only, without a test, as preregistered. The labels are the gold
reference of dev and test (the arbiter's decisions included), and the shares
carry the design weights of the gold sample with bootstrap intervals within
strata, per year of the H2 period and over the whole period. Writes
annotations/hypotheses/h2_descriptive_gold.csv.
"""

from digital_media_analysis import adjudication, annotations, gold, validation
from digital_media_analysis.config_reader import get_hypotheses
from digital_media_analysis.paths import HYPOTHESES_DIR

# The categories of the preregistered descriptive indicator of H2.
CATEGORIES = ["social_blog", "unknown", "personal"]


def main() -> None:
    first, last = get_hypotheses()["h2"]["period"]
    manifest = gold.load_manifest()
    manifest = manifest[manifest["year"].between(first, last)]
    reference, _ = annotations.gold_reference(annotations.load_labels("gold"), adjudication.load_decisions("gold"))
    reference = reference.merge(manifest[["unit_id", "platform", "split"]], on=["unit_id", "platform"])
    shares = validation.weighted_share_by_year(reference[reference["split"].isin(["dev", "test"])], manifest, "wikipedia", CATEGORIES)
    shares = shares.assign(categories=" ".join(CATEGORIES))
    HYPOTHESES_DIR.mkdir(parents=True, exist_ok=True)
    path = HYPOTHESES_DIR / "h2_descriptive_gold.csv"
    shares.to_csv(path, index=False, encoding="utf-8")
    for row in shares.itertuples(index=False):
        print(f"{row.year}: {row.share:.3f} [{row.low:.3f}, {row.high:.3f}] ({row.positives} of {row.units})")
    print(f"Written to {path}")


if __name__ == "__main__":
    main()
