"""
Vanipedia Scraper
Extracts Vedic concepts, definitions, and cross-references
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional
import httpx
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VANIPEDIA_API = "https://vanipedia.org/api"
OUTPUT_DIR = Path("./data/vanipedia_raw")
RATE_LIMIT_DELAY = 0.3


class VanipediaScraper:
    """Scrape Vedic concepts from Vanipedia"""

    def __init__(self, output_dir: Path = OUTPUT_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session: Optional[httpx.AsyncClient] = None
        self.request_count = 0
        self.last_request_time = 0
        self.concepts = {}

    async def __aenter__(self):
        self.session = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.aclose()

    async def _rate_limited_get(self, url: str, **kwargs) -> dict:
        """Rate-limited GET request"""
        import time
        elapsed = time.time() - self.last_request_time
        if elapsed < RATE_LIMIT_DELAY:
            await asyncio.sleep(RATE_LIMIT_DELAY - elapsed)

        self.request_count += 1
        if self.request_count % 10 == 0:
            logger.info(f"Vanipedia requests: {self.request_count}")

        try:
            response = await self.session.get(url, **kwargs)
            response.raise_for_status()
            self.last_request_time = time.time()
            return response.json() if response.text else {}
        except httpx.HTTPError as e:
            logger.error(f"Error fetching {url}: {e}")
            return {}

    async def search_concepts(self, query: str, limit: int = 10) -> list:
        """Search for concepts by keyword"""
        results = await self._rate_limited_get(
            f"{VANIPEDIA_API}/search",
            params={"q": query, "limit": limit}
        )
        return results.get("results", []) if results else []

    async def get_concept_details(self, concept_id: str) -> dict:
        """Fetch detailed concept information"""
        concept = await self._rate_limited_get(
            f"{VANIPEDIA_API}/concepts/{concept_id}"
        )
        return concept if concept else {}

    async def scrape_key_concepts(self):
        """Scrape key Vedic concepts"""
        logger.info("=== Vanipedia Concept Scraper ===")

        # Define core concepts to scrape
        core_concepts = [
            "Dharma", "Bhakti", "Yoga", "Karma", "Atman",
            "Brahman", "Krishna", "Arjuna", "Gita", "Vedas",
            "Samkhya", "Jnana", "Tapasya", "Moksha", "Reincarnation",
            "Varna", "Ashram", "Guna", "Maya", "Lila",
        ]

        all_concepts = {}

        for concept_name in core_concepts:
            logger.info(f"Searching: {concept_name}")
            results = await self.search_concepts(concept_name, limit=5)

            for result in results:
                concept_id = result.get("id")
                if not concept_id:
                    continue

                logger.debug(f"  Found: {result.get('title')}")

                # Get full details
                details = await self.get_concept_details(concept_id)

                if details:
                    all_concepts[concept_id] = {
                        "id": concept_id,
                        "title": details.get("title", ""),
                        "definition": details.get("definition", ""),
                        "description": details.get("content", ""),
                        "references": details.get("references", []),
                        "synonyms": details.get("synonyms", []),
                        "related_concepts": details.get("related", []),
                        "url": details.get("url", ""),
                    }

        logger.info(f"Scraped {len(all_concepts)} concepts")
        self.concepts = all_concepts
        self._save_concepts()
        return all_concepts

    def _save_concepts(self):
        """Save concepts to JSON"""
        output_file = self.output_dir / "concepts.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "metadata": {
                        "source": "vanipedia.org",
                        "scraped_at": datetime.now().isoformat(),
                        "total_concepts": len(self.concepts),
                    },
                    "concepts": self.concepts,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        logger.info(f"Saved to {output_file}")


async def main():
    async with VanipediaScraper() as scraper:
        await scraper.scrape_key_concepts()


if __name__ == "__main__":
    asyncio.run(main())
