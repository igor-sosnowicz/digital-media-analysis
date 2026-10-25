"""Frame of hypothesis H2 v2: Wikipedia articles in category trees, drawn at random per group.

For every group of `hypotheses_v2.h2.groups` (config.yaml), the articles
(namespace 0) in the listed categories and their subcategories down to
`category_depth` levels are collected breadth-first; an article reached
through several categories counts once, in the group listed first. At most
`pages_per_group` articles per group are drawn with a fixed seed. The result is
the page list of the v2 history download (scripts/00c_fetch_wikipedia_history.py).
"""

import time
from collections.abc import Callable

import numpy as np
import pandas as pd

USER_AGENT = "DigitalMediaAnalysisBot/1.0 (course project; contact via the repository)"
CATEGORY_PREFIX = "Kategoria:"


def api_get(client, api_url: str, params: dict, pause: float = 0.2) -> dict:
    """One MediaWiki API request (JSON, format version 2); raises on an API error."""
    response = client.get(api_url, params={**params, "format": "json", "formatversion": "2"})
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError(f"MediaWiki API error for {params}: {data['error']}")
    time.sleep(pause)
    return data


def category_members(get: Callable[[dict], dict], category: str, depth: int) -> pd.DataFrame:
    """Articles under `category` down to `depth` subcategory levels: title, pageid, depth, path.

    `get(params)` performs one API request and returns its JSON (continuation is handled here).
    """
    rows, seen_categories, seen_pages = [], set(), set()
    queue = [(category.removeprefix(CATEGORY_PREFIX), 0, category.removeprefix(CATEGORY_PREFIX))]
    while queue:
        name, level, path = queue.pop(0)
        if name in seen_categories:
            continue
        seen_categories.add(name)
        params = {"action": "query", "list": "categorymembers", "cmtitle": CATEGORY_PREFIX + name,
                  "cmtype": "page|subcat", "cmlimit": "max"}
        while True:
            data = get(params)
            for member in data.get("query", {}).get("categorymembers", []):
                if member["ns"] == 14 and level < depth:
                    child = member["title"].split(":", 1)[1]
                    queue.append((child, level + 1, f"{path} > {child}"))
                elif member["ns"] == 0 and member["pageid"] not in seen_pages:
                    seen_pages.add(member["pageid"])
                    rows.append({"title": member["title"], "pageid": member["pageid"], "depth": level, "path": path})
            if "continue" not in data:
                break
            params = {**params, **data["continue"]}
    return pd.DataFrame(rows, columns=["title", "pageid", "depth", "path"])


def build_frame(get: Callable[[dict], dict], groups: dict[str, list[str]], depth: int, per_group: int, seed: int) -> tuple[pd.DataFrame, dict]:
    """Drawn pages of every group (group, title, pageid, depth, path) and the size of each group before the draw."""
    rng = np.random.default_rng(seed)
    taken, parts, sizes = set(), [], {}
    for group, categories in groups.items():
        members = pd.concat([category_members(get, category, depth).assign(category=category) for category in categories],
                            ignore_index=True).drop_duplicates("pageid")
        members = members[~members["pageid"].isin(taken)]
        sizes[group] = {"pages": len(members), "categories": {category: int(members["category"].eq(category).sum()) for category in categories}}
        chosen = members if len(members) <= per_group else members.iloc[np.sort(rng.choice(len(members), size=per_group, replace=False))]
        taken.update(chosen["pageid"])
        parts.append(chosen.assign(group=group))
    frame = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=["title", "pageid", "depth", "path", "category", "group"])
    return frame[["group", "title", "pageid", "category", "depth", "path"]], sizes
