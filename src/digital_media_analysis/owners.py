"""Who runs the account behind a link to a social platform, blog or video (hypothesis H2 v2).

`account_of` extracts (platform, account) from a URL for the platforms where
the URL names the account: the first path segment (Twitter/X, Facebook,
Instagram, TikTok, Periscope, Telegram, VK), the channel or handle (YouTube,
Rumble), the subdomain (Blogspot, WordPress, Tumblr, Substack, Medium) or the
`@user` segment (Medium). A YouTube video link names no account; it becomes
`youtube.com/video:<id>` until `resolve_youtube` looks the channel up through
YouTube's public oEmbed endpoint. Owner types come from codebook/owners.yaml,
coded by people; an account not listed there is `uncoded`.
"""

import re
import time
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pandas as pd
import yaml

from digital_media_analysis.paths import PROJECT_ROOT
from digital_media_analysis.wikipedia_refs import domain

OWNERS_PATH = PROJECT_ROOT / "codebook" / "owners.yaml"
UNCODED = "uncoded"
FIRST_SEGMENT = {"twitter.com": "twitter.com", "x.com": "twitter.com", "mobile.twitter.com": "twitter.com",
                 "facebook.com": "facebook.com", "m.facebook.com": "facebook.com", "fb.com": "facebook.com",
                 "instagram.com": "instagram.com", "tiktok.com": "tiktok.com", "pscp.tv": "pscp.tv",
                 "periscope.tv": "pscp.tv", "t.me": "t.me", "vk.com": "vk.com", "rumble.com": "rumble.com",
                 "bitchute.com": "bitchute.com", "linkedin.com": "linkedin.com"}
SUBDOMAIN = ("blogspot.com", "wordpress.com", "tumblr.com", "substack.com", "medium.com", "wixsite.com", "weebly.com")
# Path segments that are not accounts.
NOT_ACCOUNTS = {"", "watch", "share", "sharer", "sharer.php", "hashtag", "search", "intent", "i", "home", "status",
                "pages", "groups", "events", "p", "reel", "explore", "embed", "video", "videos", "v", "w"}


def account_of(url: str) -> tuple[str, str] | None:
    """(platform, account) named by a link, lower case, or None for links that are not to an account's content."""
    parts = urlsplit(url if "://" in url else f"https://{url}")
    host = domain(url)
    segments = [segment for segment in parts.path.split("/") if segment]
    if host in ("youtube.com", "m.youtube.com", "youtu.be"):
        if host == "youtu.be" and segments:
            return "youtube.com", f"video:{segments[0]}"
        if segments and segments[0].startswith("@"):
            return "youtube.com", segments[0].lower()
        if len(segments) >= 2 and segments[0] in ("channel", "c", "user"):
            return "youtube.com", f"{segments[0]}/{segments[1]}".lower()
        video = parse_qs(parts.query).get("v", [None])[0] or (segments[1] if len(segments) > 1 and segments[0] in ("embed", "shorts", "live") else None)
        return ("youtube.com", f"video:{video}") if video else None
    if host in FIRST_SEGMENT:
        platform = FIRST_SEGMENT[host]
        if platform == "facebook.com" and segments[:1] == ["pages"] and len(segments) >= 2:
            return platform, segments[1].lower()
        if platform in ("rumble.com",) and len(segments) >= 2 and segments[0] in ("c", "user"):
            return platform, segments[1].lower()
        if segments and segments[0].lower() not in NOT_ACCOUNTS:
            return platform, segments[0].lstrip("@").lower()
        return None
    for platform in SUBDOMAIN:
        if host.endswith("." + platform):
            return platform, host.removesuffix("." + platform).split(".")[-1]
        if host == platform and segments and segments[0].startswith("@"):
            return platform, segments[0].lstrip("@").lower()
    return None


def key(platform: str, account: str) -> str:
    return f"{platform}/{account}".lower()


def load_owner_types(path: Path = OWNERS_PATH) -> tuple[dict[str, str], dict[str, str]]:
    """(definitions of owner types, account key -> owner type) from codebook/owners.yaml."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    types = data["owner_types"]
    accounts = {str(name).lower(): value for name, value in (data.get("accounts") or {}).items()}
    if unknown := sorted({value for value in accounts.values() if value not in types}):
        raise ValueError(f"Unknown owner types in {path}: {unknown}")
    return types, accounts


def classify(urls: pd.Series, accounts: dict[str, str]) -> pd.DataFrame:
    """Per link: platform, account and owner type (`uncoded` when the account is not coded; empty when no account)."""
    found = [account_of(url) for url in urls.fillna("").astype(str)]
    return pd.DataFrame({
        "platform": [item[0] if item else "" for item in found],
        "account": [item[1] if item else "" for item in found],
        "owner_type": [accounts.get(key(*item), UNCODED) if item else "" for item in found],
    }, index=urls.index)


def review_table(links: pd.DataFrame) -> pd.DataFrame:
    """Accounts to code, most frequent first: platform, account, key, links, pages, first and last addition, example URL."""
    with_account = links[links["account"].ne("")]
    if with_account.empty:
        return pd.DataFrame(columns=["key", "platform", "account", "links", "pages", "first_added", "last_added", "example_url", "owner_type"])
    table = with_account.groupby(["platform", "account"]).agg(
        links=("url", "size"), pages=("pageid", "nunique"), first_added=("timestamp", "min"),
        last_added=("timestamp", "max"), example_url=("url", "first"), owner_type=("owner_type", "first"),
    ).reset_index()
    table.insert(0, "key", [key(platform, account) for platform, account in zip(table["platform"], table["account"])])
    return table.sort_values(["links", "key"], ascending=[False, True], ignore_index=True)


def resolve_youtube(video_ids: list[str], client, cache: dict[str, str], pause: float = 0.5) -> dict[str, str]:
    """Channel handle or path of YouTube videos via the public oEmbed endpoint (cached; '' when unavailable)."""
    for video in video_ids:
        if video in cache:
            continue
        response = client.get("https://www.youtube.com/oembed", params={"url": f"https://www.youtube.com/watch?v={video}", "format": "json"})
        author = response.json().get("author_url", "") if response.status_code == 200 else ""
        match = re.search(r"youtube\.com/(@[^/?#]+|channel/[^/?#]+|c/[^/?#]+|user/[^/?#]+)", author)
        cache[video] = match.group(1).lower() if match else ""
        time.sleep(pause)
    return cache
