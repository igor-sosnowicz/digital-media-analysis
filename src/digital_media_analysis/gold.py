"""Draw the gold-standard sample and keep its manifest.

Sampling design (docs/plan_walidacji.md, etap 2). Each platform gets
`SAMPLE_TOTALS` units (pilot, dev and test together), split across study years
as evenly as the years allow (`year_targets`), so per-year estimates are about
equally precise:

1. Pilot: a small draw from every year, used only to calibrate the codebook. Its
   units are removed from the frame of the gold sample, so they never reach the test set.
2. Gold: the rest of each year's target, drawn at random from the remaining units.
   Reddit strata are years. Wikipedia strata are year x signal, where the signal
   is a broad, instrument-independent surface feature (`link`, `cue`, `other`);
   rare `link` units are drawn whole, `cue` is mildly oversampled and `other`
   fills the year (`split_year`). Design weights N_h / n_h undo the equal
   allocation and the oversampling in estimates.
3. Gold units are split within each stratum into `dev` (rule and prompt tuning)
   and `test` (final metrics only).

The frame is every unit created in the platform's study period (`study_periods`
in config.yaml), and only from the sources config.yaml lists: the subreddits of
`reddit_subreddits` (each in its configured years) and the pages of
`wikipedia_pages`. Each platform draws from its own random stream, so a change
in one platform's frame leaves the other platform's sample as it is. The
manifest stores identifiers and design weights only, never post text;
`sample_export` joins it with the full data.
"""

import hashlib
import json
import re
from collections.abc import Callable, Collection
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from digital_media_analysis import datasets
from digital_media_analysis.config_reader import get_reddit_subreddits, get_study_period, get_wikipedia_pages
from digital_media_analysis.paths import ANNOTATIONS_DIR, RAW_REDDIT_FRAME_DIR

SEED = 20261016

# Units per platform across all years, pilot included.
SAMPLE_TOTALS = {"reddit": 500, "wikipedia": 500}
# Pilot draws per study year.
REDDIT_PILOT_PER_YEAR = 2
WIKIPEDIA_PILOT_PER_YEAR = {"link": 0, "cue": 1, "other": 2}
# Gold `cue` units per year at most, as a share of the year's gold units: `cue`
# is about a quarter of the frame, so this oversamples it mildly.
WIKIPEDIA_GOLD_CUE_SHARE = 1 / 3
WIKIPEDIA_SIGNALS = ["link", "cue", "other"]
DEV_FRACTION = 1 / 3
# Splits annotated together in one workbook; the gold phase mixes dev and test
# so annotators cannot tell them apart. Later pilot rounds (`pilot2`, ...) drawn
# by `draw_pilot_round` also belong to the pilot phase (`phase_mask`).
PHASE_SPLITS = {"pilot": ["pilot"], "gold": ["dev", "test"]}
PILOT_ROUND = re.compile(r"pilot(\d*)")
# Row order in a phase workbook: pilot rounds follow one another, while dev and
# test are interleaved by their random `order`.
PRESENTATION_ORDER = {"pilot": ["split", "order"], "gold": ["order", "split"]}

# Text left in place of a post its author deleted or a moderator removed.
REDDIT_REMOVED_MARKERS = {"[removed]", "[deleted]"}
WIKIPEDIA_LINK = re.compile(r"https?://", re.IGNORECASE)
WIKIPEDIA_SOURCE_WORDS = re.compile(
    r"źród|przypis|\bwg\b|wedł|bada|raport|\bdane|publik|cyt|artyku|\bref\b|\blink",
    re.IGNORECASE,
)

MANIFEST_PATH = ANNOTATIONS_DIR / "sample_manifest.csv"
DESIGN_PATH = ANNOTATIONS_DIR / "sample_design.json"
MANIFEST_COLUMNS = [
    "unit_id", "platform", "phase", "split", "order", "stratum", "group", "signal", "year",
    "introduced", "N_h", "n_h", "weight",
]


def utc_year(timestamps: pd.Series) -> pd.Series:
    """Calendar year in UTC of ISO 8601 timestamps; missing for unparsable ones."""
    return pd.to_datetime(timestamps, utc=True, format="ISO8601", errors="coerce").dt.year.astype("Int64")


def reddit_units(posts: pd.DataFrame) -> pd.DataFrame:
    """One annotation unit per visible post: title, text and the post link if it leaves the thread.

    Removed posts (by moderators, filters or Reddit) and posts deleted by their
    authors are not units: they were not part of the public discussion.
    `day_weight` is the inverse probability that the post's day entered the
    frame download (1 when the download covers every day).
    """
    removed = posts["text"].isin(REDDIT_REMOVED_MARKERS) | posts["title"].isin(REDDIT_REMOVED_MARKERS)
    if "removed_by_category" in posts:  # absent from `01_fetch_reddit_data.py` downloads
        category = posts["removed_by_category"]
        removed |= category.notna() & category.astype(str).ne("")
    posts = posts[~removed]
    own_thread = pd.Series(
        [f"/comments/{post_id}/" in url for post_id, url in zip(posts["id"], posts["url"])],
        index=posts.index,
    )
    link = posts["url"].where(~own_thread, "")
    link = link.where(~link.str.startswith("/"), "https://www.reddit.com" + link)
    return pd.DataFrame({
        "unit_id": posts["id"],
        "platform": "reddit",
        "group": posts["subreddit"],
        "signal": "all",
        "year": utc_year(posts["created_at_utc"]),
        "introduced": posts["created_at_utc"],
        "title": posts["title"],
        "text": posts["text"],
        "link": link,
        "day_weight": posts["day_weight"].astype(float) if "day_weight" in posts else 1.0,
    }).sort_values("unit_id", ignore_index=True)


def wikipedia_units(revisions: pd.DataFrame) -> pd.DataFrame:
    """One annotation unit per revision with a non-empty edit summary."""
    commented = revisions[revisions["comment"].ne("")]
    # Python `re` on purpose: pandas may run str.contains on RE2, whose ASCII-only
    # \b would treat words with Polish letters differently.
    has_link = commented["comment"].map(lambda comment: bool(WIKIPEDIA_LINK.search(comment)))
    has_words = commented["comment"].map(lambda comment: bool(WIKIPEDIA_SOURCE_WORDS.search(comment)))
    return pd.DataFrame({
        "unit_id": commented["page"] + "#" + commented["revision_number"].astype(str),
        "platform": "wikipedia",
        "group": commented["page"],
        "signal": np.select([has_link, has_words], ["link", "cue"], "other"),
        "year": utc_year(commented["introduced"]),
        "introduced": commented["introduced"],
        "text": commented["comment"],
    }).sort_values("unit_id", ignore_index=True)


def load_reddit_frame() -> pd.DataFrame:
    """Frame posts of the subreddits in `reddit_subreddits` (config.yaml), each only in its configured years."""
    subreddits = get_reddit_subreddits()
    posts = datasets.load_reddit_posts(RAW_REDDIT_FRAME_DIR, subreddits=subreddits)
    years = utc_year(posts["created_at_utc"])
    active = {
        int(year): {name.casefold() for name in frame_subreddits(subreddits, int(year))}
        for year in years.dropna().unique()
    }
    keep = [not pd.isna(year) and name.casefold() in active[int(year)] for name, year in zip(posts["subreddit"], years)]
    return posts[keep].reset_index(drop=True)


def load_wikipedia_frame(with_content: Collection[tuple[str, int]] = ()) -> pd.DataFrame:
    """Revisions of the pages in `wikipedia_pages` (config.yaml); see `datasets.load_wikipedia_revisions`."""
    return datasets.load_wikipedia_revisions(with_content=with_content, pages=get_wikipedia_pages())


def load_units() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Reddit and Wikipedia units from the local data the sample is drawn from."""
    return reddit_units(load_reddit_frame()), wikipedia_units(load_wikipedia_frame())


def study_years(start: datetime, end: datetime) -> list[int]:
    """Calendar years that overlap the study period [start, end)."""
    return list(range(start.year, (end - timedelta(microseconds=1)).year + 1))


def frame_subreddits(subreddits: dict[str, tuple[int, int] | None], year: int) -> list[str]:
    """Subreddits of `reddit_subreddits` (config.yaml) that enter the Reddit frame in `year`."""
    return [name for name, years in subreddits.items() if years is None or years[0] <= year <= years[1]]


def in_study_period(units: pd.DataFrame, start: datetime, end: datetime) -> pd.DataFrame:
    introduced = pd.to_datetime(units["introduced"], utc=True, format="ISO8601", errors="coerce")
    return units[introduced.ge(start) & introduced.lt(end)]


def allocate(sizes: pd.Series, quotas: pd.Series) -> pd.Series:
    """Draws per stratum: its quota, or every unit when the stratum is smaller or the quota is None."""
    sizes = sizes.reindex(quotas.index, fill_value=0)
    return quotas.astype(float).fillna(sizes).clip(upper=sizes).astype(int)


def year_targets(sizes: pd.Series, total: int) -> pd.Series:
    """Split `total` units across years as evenly as their sizes allow.

    A year smaller than the even share is taken whole and the rest is shared
    evenly by the other years. Units that do not divide evenly go one each to
    the years with the most units, where one more draw changes the weight least.
    """
    sizes = sizes.sort_index()
    if total > sizes.sum():
        raise ValueError(f"Cannot draw {total} units from a frame of {sizes.sum()}.")
    targets = pd.Series(0, index=sizes.index)
    open_years = list(sizes.index)
    remaining = total
    while open_years:
        share = remaining // len(open_years)
        whole = [year for year in open_years if sizes[year] <= share]
        if not whole:
            break
        for year in whole:
            targets[year] = sizes[year]
            remaining -= sizes[year]
            open_years.remove(year)
    if open_years:
        share, extra = divmod(remaining, len(open_years))
        targets[open_years] = share
        largest = sizes[open_years].sort_values(ascending=False, kind="stable").index[:extra]
        targets[largest] += 1
    return targets


def split_year(total: int, available: pd.Series) -> dict[str, int]:
    """Gold draws per Wikipedia signal in one year: every `link`, `cue` up to its share, `other` for the rest.

    If `other` runs out, `cue` takes the remainder.
    """
    available = available.reindex(WIKIPEDIA_SIGNALS, fill_value=0)
    link = min(available["link"], total)
    cue = min(available["cue"], round(total * WIKIPEDIA_GOLD_CUE_SHARE), total - link)
    other = min(available["other"], total - link - cue)
    cue = min(available["cue"], total - link - other)
    return {"link": int(link), "cue": int(cue), "other": int(other)}


def _draw(units: pd.DataFrame, allocation: pd.Series, rng: np.random.Generator) -> pd.DataFrame:
    """Simple random sample of `allocation[stratum]` units from each stratum."""
    parts = []
    for stratum, n in allocation[allocation > 0].items():
        members = units[units["stratum"].eq(stratum)]
        parts.append(members.sample(n=int(n), random_state=rng).assign(N_h=len(members), n_h=int(n)))
    return pd.concat(parts, ignore_index=True)


def _split_dev_test(gold: pd.DataFrame) -> pd.DataFrame:
    """Within each stratum send the first floor(n_h * DEV_FRACTION) draws to dev, the rest to test."""
    position = gold.groupby("stratum").cumcount()
    n_dev = np.floor(gold["n_h"] * DEV_FRACTION).astype(int)
    gold = gold.assign(split=np.where(position < n_dev, "dev", "test"))
    # Design weights per split: each split is itself a stratified sample of the frame.
    n_split = gold.groupby(["stratum", "split"])["unit_id"].transform("size")
    return gold.assign(n_h=n_split, weight=gold["N_h"] / n_split)


def _sample_platform(
    units: pd.DataFrame,
    pilot_quotas: pd.Series,
    gold_quotas: Callable[[pd.DataFrame, pd.Series], pd.Series],
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Pilot, then gold from the units the pilot left.

    `gold_quotas(frame, pilot_per_year)` returns the gold draws per stratum.
    """
    pilot = _draw(units, allocate(units["stratum"].value_counts(), pilot_quotas), rng)
    pilot = pilot.assign(phase="pilot", split="pilot", weight=pilot["N_h"] / pilot["n_h"])

    frame = units[~units["unit_id"].isin(pilot["unit_id"])]
    allocation = gold_quotas(frame, pilot.groupby("year").size())
    gold = _split_dev_test(_draw(frame, allocation, rng).assign(phase="gold"))

    sample = pd.concat([pilot, gold], ignore_index=True)
    # Presentation order: random, but fixed, within each split.
    sample["order"] = (
        sample.assign(key=rng.permutation(len(sample)))
        .groupby("split")["key"].rank(method="first").astype(int)
    )
    return sample


def draw_sample(
    reddit: pd.DataFrame,
    wikipedia: pd.DataFrame,
    seed: int = SEED,
    periods: dict[str, tuple[datetime, datetime]] | None = None,
    totals: dict[str, int] | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Return the manifest (one row per sampled unit) and a description of the design.

    Each platform has its own study period (`study_periods` in config.yaml), because
    each tests a hypothesis about different years.
    """
    periods = periods or {platform: get_study_period(platform) for platform in SAMPLE_TOTALS}
    totals = totals or SAMPLE_TOTALS
    years = {platform: study_years(*period) for platform, period in periods.items()}
    reddit_rng, wikipedia_rng = (np.random.default_rng(stream) for stream in np.random.SeedSequence(seed).spawn(2))

    reddit_years = years["reddit"]
    reddit = in_study_period(reddit, *periods["reddit"])
    reddit = reddit.assign(stratum=reddit["year"].astype(str))
    reddit_targets = year_targets(
        reddit.groupby("year").size().reindex(reddit_years, fill_value=0), totals["reddit"]
    )

    def reddit_gold(frame: pd.DataFrame, pilot_per_year: pd.Series) -> pd.Series:
        gold = reddit_targets - pilot_per_year.reindex(reddit_years, fill_value=0)
        return gold.clip(lower=0).set_axis([str(year) for year in reddit_years])

    reddit_sample = _sample_platform(
        reddit,
        pilot_quotas=pd.Series(REDDIT_PILOT_PER_YEAR, index=[str(year) for year in reddit_years]),
        gold_quotas=reddit_gold,
        rng=reddit_rng,
    )
    # The frame holds only posts of drawn days: a post stands for N_h / n_h frame
    # posts, and each frame post for `day_weight` posts of its month.
    reddit_sample = reddit_sample.assign(weight=reddit_sample["weight"] * reddit_sample["day_weight"])

    wikipedia_years = years["wikipedia"]
    wikipedia = in_study_period(wikipedia, *periods["wikipedia"])
    wikipedia = wikipedia.assign(stratum=wikipedia["year"].astype(str) + "|" + wikipedia["signal"])
    wikipedia_targets = year_targets(
        wikipedia.groupby("year").size().reindex(wikipedia_years, fill_value=0), totals["wikipedia"]
    )

    def wikipedia_gold(frame: pd.DataFrame, pilot_per_year: pd.Series) -> pd.Series:
        quotas = {}
        for year in wikipedia_years:
            gold_total = max(int(wikipedia_targets[year] - pilot_per_year.get(year, 0)), 0)
            available = frame.loc[frame["year"].eq(year), "signal"].value_counts()
            for signal, n in split_year(gold_total, available).items():
                quotas[f"{year}|{signal}"] = n
        return pd.Series(quotas)

    wikipedia_sample = _sample_platform(
        wikipedia,
        pilot_quotas=pd.Series(
            {f"{year}|{signal}": WIKIPEDIA_PILOT_PER_YEAR[signal] for year in wikipedia_years for signal in WIKIPEDIA_SIGNALS}
        ),
        gold_quotas=wikipedia_gold,
        rng=wikipedia_rng,
    )

    manifest = pd.concat([reddit_sample, wikipedia_sample], ignore_index=True)[MANIFEST_COLUMNS]
    manifest = manifest.astype({"year": int}).sort_values(["platform", "split", "order"], ignore_index=True)
    frames = {"reddit": reddit, "wikipedia": wikipedia}
    targets = {"reddit": reddit_targets, "wikipedia": wikipedia_targets}
    design = {
        "seed": seed,
        "created_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "study_period": {
            platform: {"start": start.isoformat(), "end": end.isoformat(), "years": years[platform]}
            for platform, (start, end) in periods.items()
        },
        "reddit": {
            "strata": "year",
            "frame": "posts not removed or deleted, on drawn days or in whole years, data/raw/reddit_frame",
            "subreddits": {name: list(window) if window else None for name, window in get_reddit_subreddits().items()},
            "pilot_per_year": REDDIT_PILOT_PER_YEAR,
            # Frame posts scaled up by their day weights: the posts each year is estimated to have.
            "estimated_posts_per_year": {
                str(year): round(float(weight)) for year, weight in reddit.groupby("year")["day_weight"].sum().items()
            },
        },
        "wikipedia": {
            "strata": "year x signal",
            "frame": "revisions with a non-empty edit summary, data/raw/wikipedia",
            "pages": get_wikipedia_pages(),
            "pilot_per_year": WIKIPEDIA_PILOT_PER_YEAR,
            "gold_cue_share": WIKIPEDIA_GOLD_CUE_SHARE,
            "link_pattern": WIKIPEDIA_LINK.pattern,
            "source_words_pattern": WIKIPEDIA_SOURCE_WORDS.pattern,
        },
        "dev_fraction": DEV_FRACTION,
        "population": {platform: population_fingerprint(frame) for platform, frame in frames.items()},
        "allocation": {
            platform: {
                "total": totals[platform],
                "per_year": {str(year): int(n) for year, n in targets[platform].items()},
                # Years too small for an even share, drawn whole.
                "whole_years": [
                    int(year) for year, n in targets[platform].items()
                    if n == frames[platform]["year"].eq(year).sum()
                ],
            }
            for platform in frames
        },
        "sample_sizes": {
            platform: frame["split"].value_counts().sort_index().to_dict()
            for platform, frame in manifest.groupby("platform")
        },
        "per_year": {
            platform: {str(year): row for year, row in year_summary(manifest, platform).to_dict(orient="index").items()}
            for platform in frames
        },
    }
    return manifest, design


def phase_mask(manifest: pd.DataFrame, phase: str) -> pd.Series:
    """Manifest rows of a phase; every pilot round (`pilot`, `pilot2`, ...) belongs to the pilot."""
    split = manifest["split"].astype(str)
    if phase == "pilot":
        return split.str.fullmatch(PILOT_ROUND.pattern)
    return split.isin(PHASE_SPLITS[phase])


def next_pilot_round(manifest: pd.DataFrame) -> str:
    """Split name of the next pilot round: `pilot2` after the first pilot, then `pilot3`, ..."""
    rounds = [int(match.group(1) or 1) for split in manifest["split"].astype(str) if (match := PILOT_ROUND.fullmatch(split))]
    return f"pilot{max(rounds, default=1) + 1}"


def draw_pilot_round(
    manifest: pd.DataFrame,
    units: dict[str, pd.DataFrame],
    counts: dict[str, int],
    split: str,
    seed: int = SEED,
    periods: dict[str, tuple[datetime, datetime]] | None = None,
) -> pd.DataFrame:
    """Manifest rows of another pilot round: `counts[platform]` fresh units from outside the sample.

    The units come from the same frame as the sample but from none of its splits,
    so calibrating the codebook on them never touches dev or test. Each platform's
    count is spread over its study years as evenly as the remaining units allow
    (`year_targets`); within a Wikipedia year a third goes to `cue` and the rest
    to `other`, as `split_year` does without links (all links are in the gold
    sample). Weights N_h / n_h refer to the units left outside the sample.
    """
    periods = periods or {platform: get_study_period(platform) for platform in counts}
    round_number = int(PILOT_ROUND.fullmatch(split).group(1) or 1)
    # A stream per round and platform, independent of the main draw.
    streams = np.random.SeedSequence([seed, round_number]).spawn(len(SAMPLE_TOTALS))
    rngs = {platform: np.random.default_rng(stream) for platform, stream in zip(SAMPLE_TOTALS, streams)}
    taken = set(manifest["unit_id"].astype(str))
    parts = []
    for platform, count in counts.items():
        if count <= 0:
            continue
        years = study_years(*periods[platform])
        remaining = in_study_period(units[platform], *periods[platform])
        remaining = remaining[~remaining["unit_id"].astype(str).isin(taken)]
        targets = year_targets(remaining.groupby("year").size().reindex(years, fill_value=0), count)
        if platform == "wikipedia":
            remaining = remaining.assign(stratum=remaining["year"].astype(str) + "|" + remaining["signal"])
            allocation = {}
            for year, total in targets.items():
                available = remaining.loc[remaining["year"].eq(year) & remaining["signal"].ne("link"), "signal"].value_counts()
                for signal, n in split_year(int(total), available).items():
                    allocation[f"{year}|{signal}"] = n
            allocation = pd.Series(allocation)
        else:
            remaining = remaining.assign(stratum=remaining["year"].astype(str))
            allocation = targets.set_axis([str(year) for year in targets.index])
        rng = rngs[platform]
        drawn = _draw(remaining, allocation, rng)
        weight = drawn["N_h"] / drawn["n_h"] * (drawn["day_weight"] if "day_weight" in drawn else 1.0)
        drawn = drawn.assign(phase="pilot", split=split, weight=weight, order=rng.permutation(len(drawn)) + 1)
        parts.append(drawn)
    if not parts:
        return pd.DataFrame(columns=MANIFEST_COLUMNS)
    rows = pd.concat(parts, ignore_index=True)[MANIFEST_COLUMNS]
    return rows.astype({"year": int}).sort_values(["platform", "order"], ignore_index=True)


def population_fingerprint(units: pd.DataFrame) -> dict:
    """Size and hash of the sampled population, to detect a changed data snapshot."""
    keys = "\n".join(sorted(units["unit_id"] + "@" + units["introduced"]))
    return {"units": len(units), "sha256": hashlib.sha256(keys.encode("utf-8")).hexdigest()}


def save_sample(
    manifest: pd.DataFrame,
    design: dict,
    manifest_path: Path = MANIFEST_PATH,
    design_path: Path = DESIGN_PATH,
    force: bool = False,
) -> None:
    """Write the manifest and design; refuse to replace an existing sample unless forced."""
    if manifest_path.exists() and not force:
        raise FileExistsError(
            f"{manifest_path} already exists. Redrawing changes the gold sample after "
            "annotation has started; pass force=True (script: --force) only if that is intended."
        )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(manifest_path, index=False, encoding="utf-8")
    design_path.write_text(json.dumps(design, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_manifest(manifest_path: Path = MANIFEST_PATH) -> pd.DataFrame:
    if not manifest_path.exists():
        raise FileNotFoundError(f"{manifest_path} not found; run `make gold-sample`.")
    return pd.read_csv(manifest_path, dtype={"unit_id": str, "stratum": str, "introduced": str})


def attach_units(manifest: pd.DataFrame, units: pd.DataFrame) -> pd.DataFrame:
    """Join manifest rows with unit text, failing if the local data no longer matches."""
    columns = [column for column in units.columns if column not in manifest.columns or column == "unit_id"]
    joined = manifest.merge(units[columns], on="unit_id", how="left", indicator=True)
    missing = joined.loc[joined["_merge"].ne("both"), "unit_id"].tolist()
    if missing:
        raise ValueError(
            f"{len(missing)} sampled units are missing from the local data (e.g. {missing[:3]}). "
            "The data snapshot differs from the one the sample was drawn from."
        )
    current = units.set_index("unit_id")["introduced"]
    changed = joined[joined["unit_id"].map(current).ne(joined["introduced"])]["unit_id"].tolist()
    if changed:
        raise ValueError(
            f"{len(changed)} sampled units have a different timestamp in the local data "
            f"(e.g. {changed[:3]}); revision numbering has shifted."
        )
    return joined.drop(columns="_merge")


def design_summary(manifest: pd.DataFrame, platform: str) -> pd.DataFrame:
    """Per-stratum population size, draws per split and test weight, for notebooks and slides."""
    gold = manifest[manifest["platform"].eq(platform) & manifest["phase"].eq("gold")]
    return pd.concat(
        [
            gold.groupby("stratum")["N_h"].first().rename("N_h (rama)"),
            pd.crosstab(gold["stratum"], gold["split"]).reindex(columns=["dev", "test"], fill_value=0),
            gold[gold["split"].eq("test")].groupby("stratum")["weight"].first().rename("waga test"),
        ],
        axis=1,
    )


def year_summary(manifest: pd.DataFrame, platform: str) -> pd.DataFrame:
    """Units in the frame and draws per split for every year: the check that years are balanced."""
    rows = manifest[manifest["platform"].eq(platform)]
    gold = rows[rows["phase"].eq("gold")]
    # The gold frame of a stratum is what the first pilot left, so add that pilot
    # back; later pilot rounds come from inside the gold frame and are not added.
    frame = gold.groupby("stratum").first().groupby("year")["N_h"].sum()
    pilots = sorted({"pilot", *(split for split in rows["split"].unique() if PILOT_ROUND.fullmatch(str(split)))})
    draws = pd.crosstab(rows["year"], rows["split"]).reindex(columns=[*pilots, "dev", "test"], fill_value=0)
    summary = pd.concat([(frame.add(draws["pilot"], fill_value=0)).rename("N (rama)"), draws], axis=1)
    return summary.fillna(0).astype(int).rename_axis("year")
