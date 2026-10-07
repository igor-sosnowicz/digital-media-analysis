"""Scraper Wikipedia for edits on specified pages."""

import asyncio
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlsplit

import httpx
from tqdm.auto import tqdm

from digital_media_analysis.data_models import Revision, WikipediaPage


class WikipediaScraper:
    START = "2016-01-01T00:00:00Z"
    USER_AGENT = "DigitalMediaAnalysisBot/1.0 (contact: 263897@student.pwr.edu.pl)"

    def __init__(self, max_concurrent_pages: int = 3) -> None:
        self._semaphore = __import__("asyncio").Semaphore(max_concurrent_pages)

    @staticmethod
    def _parse_page(page: str) -> tuple[str, str, str]:
        """Return (API endpoint, title, page URL) for a Wikipedia URL or title."""
        if "://" not in page:
            title = page.replace("_", " ").strip()
            host = "en.wikipedia.org"
            page_url = (
                f"https://{host}/wiki/{quote(title.replace(' ', '_'), safe='()_,:-')}"
            )
        else:
            parsed = urlsplit(page)
            host = parsed.hostname or ""

            if not (host == "wikipedia.org" or host.endswith(".wikipedia.org")):
                raise ValueError(f"Not a Wikipedia URL: {page}")

            query_title = parse_qs(parsed.query).get("title", [None])[0]
            if query_title:
                title = query_title.replace("_", " ").strip()
            elif parsed.path.startswith("/wiki/"):
                title = unquote(parsed.path[len("/wiki/") :]).replace("_", " ").strip()
            else:
                raise ValueError(f"Could not extract a page title from: {page}")

            page_url = (
                f"https://{host}/wiki/{quote(title.replace(' ', '_'), safe='()_,:-')}"
            )

        if not title:
            raise ValueError(f"Empty Wikipedia page title: {page}")

        return f"https://{host}/w/api.php", title, page_url

    async def _scrape_one(
        self,
        client: httpx.AsyncClient,
        page: str,
    ) -> WikipediaPage:
        api_url, title, page_url = self._parse_page(page)
        end = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        params = {
            "action": "query",
            "prop": "revisions",
            "titles": title,
            "rvprop": "timestamp|content",
            "rvslots": "main",
            "rvstart": end,
            "rvend": self.START,
            "rvdir": "older",
            "rvlimit": "max",
            "format": "json",
            "formatversion": "2",
        }

        revisions: list[Revision] = []

        async with self._semaphore:
            while True:
                response = await client.get(api_url, params=params)
                response.raise_for_status()
                data = response.json()

                if "error" in data:
                    raise RuntimeError(
                        f"MediaWiki API error for {page}: {data['error']}"
                    )

                for result_page in data.get("query", {}).get("pages", []):
                    for revision in result_page.get("revisions", []):
                        slot = revision.get("slots", {}).get("main", {})
                        content = slot.get("content", slot.get("*", ""))

                        revisions.append(
                            Revision(
                                new_content=content,
                                introduced=datetime.fromisoformat(
                                    revision["timestamp"]
                                ),
                            )
                        )

                continuation = data.get("continue")
                if not continuation:
                    break
                params.update(continuation)

        revisions.sort(key=lambda revision: revision.introduced)
        return WikipediaPage(url=page_url, edits=revisions)

    async def scrape(self, pages: list[str]) -> list[WikipediaPage]:
        headers = {"User-Agent": self.USER_AGENT}

        async with httpx.AsyncClient(
            headers=headers,
            timeout=httpx.Timeout(60.0),
        ) as client:
            with tqdm(
                total=len(pages), desc="Scraping Wikipedia", unit="page"
            ) as progress:

                async def scrape_with_progress(page: str) -> WikipediaPage:
                    try:
                        return await self._scrape_one(client, page)
                    finally:
                        progress.update(1)

                return await asyncio.gather(
                    *(scrape_with_progress(page) for page in pages)
                )


def save_wikipedia_results(
    results: list[WikipediaPage],
    output_dir: str | Path = "./data/raw/wikipedia",
) -> list[Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    saved_paths = []

    for result in results:
        title = unquote(urlsplit(result.url).path.rsplit("/", 1)[-1])
        filename = re.sub(r"[^\w.-]+", "_", title, flags=re.UNICODE).strip("._")
        file_path = output_path / f"{filename or 'wikipedia_page'}.json"

        file_path.write_text(
            result.model_dump_json(indent=2),
            encoding="utf-8",
        )
        saved_paths.append(file_path)

    return saved_paths
