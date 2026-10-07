"""Script for fetching configured Wikipedia pages into the `./data` directory."""

import asyncio

from digital_media_analysis.config_reader import get_config
from digital_media_analysis.wikipedia_scraper import (
    WikipediaScraper,
    save_wikipedia_results,
)


async def main() -> None:
    pages = get_config("wikipedia_pages")
    if not isinstance(pages, list) or not all(isinstance(page, str) for page in pages):
        raise ValueError("'wikipedia_pages' must be a list of URLs in config.yaml.")

    wiki_scraper = WikipediaScraper()
    results = await wiki_scraper.scrape(pages)
    save_wikipedia_results(results)


if __name__ == "__main__":
    asyncio.run(main())
