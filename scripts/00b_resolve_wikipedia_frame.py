"""Resolve the frame of H2 v2: articles in the category trees of `hypotheses_v2.h2.groups`, drawn per group.

Writes annotations/hypotheses_v2/h2_pages.csv (group, title, pageid, the
category it was found under, depth, path) and h2_frame_sizes.json (articles per
group and category before the draw; a category with no articles is reported,
as its name may be wrong). Needs the committed preregistration v2 and network
access to the Wikipedia API. The page list defines the frame, so an existing
one is kept unless --force.
"""

import argparse
import json
from datetime import UTC, datetime

import httpx

from digital_media_analysis.config_reader import get_hypotheses_v2
from digital_media_analysis.paths import HYPOTHESES_V2_DIR
from digital_media_analysis.prereg import require_committed
from digital_media_analysis.wikipedia_frame import USER_AGENT, api_get, build_frame

SEED = 20261025


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Resolve again and overwrite the page list.")
    args = parser.parse_args()
    commit = require_committed()
    settings = get_hypotheses_v2()["h2"]
    output = HYPOTHESES_V2_DIR / "h2_pages.csv"
    if output.exists() and not args.force:
        parser.error(f"{output} exists and defines the frame; use --force to resolve it again.")
    api = f"https://{settings['wiki']}/w/api.php"
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=60) as client:
        frame, sizes = build_frame(lambda params: api_get(client, api, params), settings["groups"],
                                   settings["category_depth"], settings["pages_per_group"], SEED)
    HYPOTHESES_V2_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False, encoding="utf-8")
    empty = [category for group in sizes.values() for category, count in group["categories"].items() if count == 0]
    log = {"resolved_utc": datetime.now(UTC).isoformat(timespec="seconds"), "commit": commit, "seed": SEED,
           "wiki": settings["wiki"], "depth": settings["category_depth"], "pages_per_group": settings["pages_per_group"],
           "sizes": sizes, "categories_without_articles": empty}
    (HYPOTHESES_V2_DIR / "h2_frame_sizes.json").write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for group, size in sizes.items():
        print(f"{group}: {size['pages']} articles, {int(frame['group'].eq(group).sum())} drawn")
    if empty:
        print(f"Categories without articles (check their names): {empty}")


if __name__ == "__main__":
    main()
