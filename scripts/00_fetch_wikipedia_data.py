"""Script for fetching configured Wikipedia pages into the `./data` directory."""

import asyncio

from digital_media_analysis.config_reader import get_wikipedia_pages
from digital_media_analysis.wikipedia_scraper import (
    WikipediaScraper,
    save_wikipedia_results,
)


async def main() -> None:
    pages = get_wikipedia_pages()

    wiki_scraper = WikipediaScraper()
    results = await wiki_scraper.scrape(pages)
    save_wikipedia_results(results)


if __name__ == "__main__":
    asyncio.run(main())
