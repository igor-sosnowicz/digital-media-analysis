"""H2 v2: links added to the frame's articles and talk pages, with the three definitions of an alternative source.

From the histories in data/raw/wikipedia_v2/ it writes
annotations/hypotheses_v2/h2_links.csv: one row per link addition (page, group,
namespace, revision, time, anonymous editor, URL, domain, first addition,
added in a reverted edit, days the link stayed, censoring), with:
- the domain category of codebook/domains.yaml and `alt_domain` (the v1 definition);
- platform, account and owner type of codebook/owners.yaml and `alt_owner`;
- the perennial-sources status (codebook/rsp_domains.csv) and `alt_rsp`.
It also writes owner_review.csv, the accounts people still have to code, most
frequent first. Optional network steps: --fetch-rsp downloads and parses the
perennial-sources list; --resolve-youtube looks up the channels of video links.
"""

import argparse
import json

import httpx
import pandas as pd

from digital_media_analysis import owners, rsp, wikipedia_history, wikipedia_refs
from digital_media_analysis.config_reader import get_hypotheses_v2
from digital_media_analysis.paths import DATA_DIR, HYPOTHESES_V2_DIR, RAW_WIKIPEDIA_V2_DIR
from digital_media_analysis.wikipedia_frame import USER_AGENT, api_get

YOUTUBE_CACHE = DATA_DIR / "external" / "youtube_channels.json"


def fetch_rsp() -> None:
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=60) as client:
        data = api_get(client, "https://en.wikipedia.org/w/api.php",
                       {"action": "parse", "page": rsp.PAGE, "prop": "wikitext"})
    wikitext = data["parse"]["wikitext"]
    raw = DATA_DIR / "external" / "rsp.wikitext"
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_text(wikitext, encoding="utf-8")
    table = rsp.parse(wikitext)
    table.to_csv(rsp.RSP_PATH, index=False, encoding="utf-8")
    print(f"Perennial sources: {len(table)} domains -> {rsp.RSP_PATH} ({table['status'].value_counts().to_dict()})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch-rsp", action="store_true", help="Download and parse the perennial-sources list first.")
    parser.add_argument("--resolve-youtube", action="store_true", help="Look up the channels of YouTube video links (network).")
    args = parser.parse_args()
    settings = get_hypotheses_v2()["h2"]
    if args.fetch_rsp:
        fetch_rsp()

    pages = pd.read_csv(HYPOTHESES_V2_DIR / "h2_pages.csv")
    groups = dict(zip(pages["pageid"], pages["group"]))
    end = json.loads((RAW_WIKIPEDIA_V2_DIR / "fetch_log.json").read_text(encoding="utf-8"))
    stop = max(entry["end"] for entry in end["pages"].values())
    events = []
    for namespace in settings["namespaces"]:
        for path in sorted((RAW_WIKIPEDIA_V2_DIR / str(namespace)).glob("*.jsonl.gz")):
            records = wikipedia_history.load_records([path])
            if records:
                table = wikipedia_history.link_events(sorted(records, key=lambda record: (record["timestamp"], record["revid"])), stop)
                events.append(table.assign(article=int(path.name.split(".")[0])))
    links = pd.concat(events, ignore_index=True)
    when = pd.to_datetime(links["timestamp"], utc=True)
    links = links.assign(group=links["article"].map(groups), year=when.dt.year, month=when.dt.strftime("%Y-%m"))

    links["category"] = wikipedia_refs.categorise(links["domain"], wikipedia_refs.load_domain_categories())
    _, accounts = owners.load_owner_types()
    found = owners.classify(links["url"], accounts)
    if args.resolve_youtube:
        cache = json.loads(YOUTUBE_CACHE.read_text(encoding="utf-8")) if YOUTUBE_CACHE.exists() else {}
        videos = sorted({account.removeprefix("video:") for account in found["account"] if account.startswith("video:")})
        with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30) as client:
            cache = owners.resolve_youtube(videos, client, cache)
        YOUTUBE_CACHE.parent.mkdir(parents=True, exist_ok=True)
        YOUTUBE_CACHE.write_text(json.dumps(cache, indent=1) + "\n", encoding="utf-8")
        resolved = found["account"].map(lambda account: cache.get(account.removeprefix("video:"), "") if account.startswith("video:") else "")
        found.loc[resolved.ne(""), "account"] = resolved[resolved.ne("")]
        found["owner_type"] = [accounts.get(owners.key(platform, account), owners.UNCODED) if account else ""
                               for platform, account in zip(found["platform"], found["account"])]
    links = pd.concat([links, found], axis=1)
    statuses = rsp.load() if rsp.RSP_PATH.exists() else {}
    links["rsp_status"] = rsp.status_of(links["domain"], statuses)
    links = links.assign(
        alt_domain=links["category"].isin(settings["alternative_categories"]).astype(int),
        alt_owner=links["owner_type"].isin(settings["alternative_owner_types"]).astype(int),
        uncoded_owner=links["owner_type"].eq(owners.UNCODED).astype(int),
        alt_rsp=links["rsp_status"].isin(settings["unreliable_rsp_statuses"]).astype(int),
    )
    HYPOTHESES_V2_DIR.mkdir(parents=True, exist_ok=True)
    links.to_csv(HYPOTHESES_V2_DIR / "h2_links.csv", index=False, encoding="utf-8")
    review = owners.review_table(links)
    review.to_csv(HYPOTHESES_V2_DIR / "owner_review.csv", index=False, encoding="utf-8")
    print(f"{len(links)} link additions on {links['article'].nunique()} pages; accounts to code: "
          f"{int(review['owner_type'].eq(owners.UNCODED).sum())} of {len(review)}; RSP list: {'yes' if statuses else 'missing (--fetch-rsp)'}")


if __name__ == "__main__":
    main()
