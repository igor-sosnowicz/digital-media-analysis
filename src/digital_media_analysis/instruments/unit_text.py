"""The text an instrument reads for each annotation unit, built as the codebook defines the unit.

Reddit: title, body and the post link when it leaves the thread (codebook `units`).
Links to images and videos the platform hosts for the author are left out, as
they are never a source (rule R3). Wikipedia: the edit summary without the
automatic `/* section */` prefix, which only names the edited section (rule R9).
"""

import re
from urllib.parse import urlsplit

import pandas as pd

# Hosts of the author's own pictures and videos (codebook rule R3).
OWN_MEDIA_HOSTS = {"i.redd.it", "v.redd.it", "preview.redd.it", "imgur.com", "i.imgur.com", "m.imgur.com"}
SECTION_PREFIX = re.compile(r"/\*.*?\*/")
MAX_BODY_CHARS = 1500
MAX_LINK_CHARS = 200


def link_host(url: str) -> str:
    """Lower-case host of a URL without `www.` ('' when there is none)."""
    host = urlsplit(url if "://" in url else f"https://{url}").netloc.lower()
    return host.removeprefix("www.")


def reddit_text(title: str, body: str, link: str) -> str:
    """Title, the start of the body and the post link, unless it points to the author's own media."""
    parts = [title.strip()]
    if body.strip():
        parts.append(body.strip()[:MAX_BODY_CHARS])
    if link and link_host(link) not in OWN_MEDIA_HOSTS:
        parts.append(f"Link: {link[:MAX_LINK_CHARS]}")
    return "\n".join(part for part in parts if part)


def wikipedia_text(comment: str) -> str:
    """The edit summary without the automatic section prefix."""
    return re.sub(r"\s+", " ", SECTION_PREFIX.sub(" ", comment)).strip()


def unit_texts(units: pd.DataFrame) -> pd.Series:
    """Instrument input per unit, indexed by `unit_id`; units of both platforms may be mixed."""
    frame = units.reindex(columns=["platform", "title", "text", "link"]).fillna("").astype(str)
    texts = [
        reddit_text(row.title, row.text, row.link) if row.platform == "reddit" else wikipedia_text(row.text)
        for row in frame.itertuples(index=False)
    ]
    return pd.Series(texts, index=units["unit_id"].astype(str), name="text")
