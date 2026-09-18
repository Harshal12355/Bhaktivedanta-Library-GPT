"""
Vanipedia Scraper
Extracts Vedic concepts, definitions, and cross-references

NOTE: vanipedia.org never had the REST API this scraper originally targeted
(https://vanipedia.org/api/search, /api/concepts/<id>) - those endpoints
don't exist and always 404'd. Vanipedia is a standard MediaWiki install, so
this version uses its real API (/w/api.php): action=query&list=search to
find the best-matching article for each concept, then
action=query&prop=revisions to fetch its wikitext, which is cleaned with
mwparserfromhell into plain text.
"""

import asyncio
import json
import logging
import re
import time
from pathlib import Path
from typing import Optional
import httpx
import mwparserfromhell
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VANIPEDIA_API = "https://vanipedia.org/w/api.php"
OUTPUT_DIR = Path("./data/vanipedia_raw")
RATE_LIMIT_DELAY = 1.0
USER_AGENT = "BhaktivedantaLibraryGPT-Research/1.0 (+personal study/RAG project)"
# Vanipedia is multilingual; non-English articles live in namespace 0 too, under a
# "<LANGCODE>/" title prefix (e.g. "ES/Prabhupada 0275 - ..."). Filter those out.
NON_ENGLISH_PREFIX_RE = re.compile(r"^[A-Z]{2,3}/")


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
        self.session = httpx.AsyncClient(timeout=30.0, headers={"User-Agent": USER_AGENT})
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.aclose()

    async def _rate_limited_get(self, params: dict) -> dict:
        """Rate-limited GET request against the MediaWiki API"""
        elapsed = time.time() - self.last_request_time
        if elapsed < RATE_LIMIT_DELAY:
            await asyncio.sleep(RATE_LIMIT_DELAY - elapsed)

        self.request_count += 1
        if self.request_count % 10 == 0:
            logger.info(f"Vanipedia requests: {self.request_count}")

        try:
            response = await self.session.get(VANIPEDIA_API, params={**params, "format": "json"})
            response.raise_for_status()
            self.last_request_time = time.time()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error fetching {params}: {e}")
            return {}

    async def search_concepts(self, query: str, limit: int = 10) -> list:
        """Search for concepts by keyword"""
        data = await self._rate_limited_get({
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": limit * 3,  # over-fetch since non-English hits get filtered out
            "srnamespace": 0,
        })
        results = data.get("query", {}).get("search", [])
        results = [r for r in results if not NON_ENGLISH_PREFIX_RE.match(r.get("title", ""))]
        return results[:limit]

    async def get_concept_details(self, title: str) -> dict:
        """Fetch a page's wikitext and clean it into plain text"""
        data = await self._rate_limited_get({
            "action": "query",
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main",
            "titles": title,
        })
        pages = data.get("query", {}).get("pages", {})
        for page_id, page in pages.items():
            if page_id == "-1" or "revisions" not in page:
                continue
            wikitext = page["revisions"][0]["slots"]["main"]["*"]
            parsed = mwparserfromhell.parse(wikitext)
            plain_text = parsed.strip_code().strip()
            return {
                "pageid": page.get("pageid"),
                "title": page.get("title", title),
                "content": plain_text,
                "url": f"https://vanipedia.org/wiki/{page.get('title', title).replace(' ', '_')}",
            }
        return {}

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
            results = await self.search_concepts(concept_name, limit=3)

            for result in results:
                title = result.get("title")
                if not title:
                    continue

                logger.info(f"  Found: {title}")
                details = await self.get_concept_details(title)

                if details:
                    concept_id = str(details["pageid"])
                    all_concepts[concept_id] = {
                        "id": concept_id,
                        "title": details.get("title", ""),
                        "definition": details.get("content", "")[:500],
                        "description": details.get("content", ""),
                        "references": [],
                        "synonyms": [],
                        "related_concepts": [concept_name],
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
