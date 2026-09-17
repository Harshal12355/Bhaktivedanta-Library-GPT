"""
VedaBase Comprehensive Scraper
Fetches all English books, chapters, verses, and commentaries from vedabase.io
"""

import asyncio
import json
import time
from typing import Optional
from pathlib import Path
import httpx
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VEDABASE_API = "https://vedabase.io/api"
RATE_LIMIT_DELAY = 0.2  # 200ms between requests to be respectful
OUTPUT_DIR = Path("./data/vedabase_raw")


class VedaBaseScraper:
    def __init__(self, output_dir: Path = OUTPUT_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session: Optional[httpx.AsyncClient] = None
        self.request_count = 0
        self.last_request_time = 0

    async def __aenter__(self):
        self.session = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, *args):
        await self.session.aclose()

    async def _rate_limited_get(self, url: str, **kwargs) -> dict:
        """Rate-limited GET request"""
        elapsed = time.time() - self.last_request_time
        if elapsed < RATE_LIMIT_DELAY:
            await asyncio.sleep(RATE_LIMIT_DELAY - elapsed)

        self.request_count += 1
        if self.request_count % 10 == 0:
            logger.info(f"Requests made: {self.request_count}")

        try:
            response = await self.session.get(url, **kwargs)
            response.raise_for_status()
            self.last_request_time = time.time()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error fetching {url}: {e}")
            return {}

    async def get_all_books(self) -> list:
        """Fetch all available books with language=en"""
        logger.info("Fetching all English books...")
        books_data = await self._rate_limited_get(
            f"{VEDABASE_API}/books/?language=en"
        )
        books = books_data.get("results", [])

        # Handle pagination
        while books_data.get("next"):
            next_page = books_data.get("next", "").replace(VEDABASE_API, "")
            books_data = await self._rate_limited_get(f"{VEDABASE_API}{next_page}")
            books.extend(books_data.get("results", []))

        logger.info(f"Found {len(books)} English books")
        return books

    async def get_book_chapters(self, book_id: str) -> list:
        """Fetch all chapters for a book"""
        chapters_data = await self._rate_limited_get(
            f"{VEDABASE_API}/books/{book_id}/chapters/?language=en"
        )
        chapters = chapters_data.get("results", [])

        while chapters_data.get("next"):
            next_page = chapters_data.get("next", "").replace(VEDABASE_API, "")
            chapters_data = await self._rate_limited_get(
                f"{VEDABASE_API}{next_page}"
            )
            chapters.extend(chapters_data.get("results", []))

        return chapters

    async def get_chapter_verses(self, book_id: str, chapter_number: int) -> list:
        """Fetch all verses in a chapter"""
        verses_data = await self._rate_limited_get(
            f"{VEDABASE_API}/books/{book_id}/chapters/{chapter_number}/verses/?language=en"
        )
        verses = verses_data.get("results", [])

        while verses_data.get("next"):
            next_page = verses_data.get("next", "").replace(VEDABASE_API, "")
            verses_data = await self._rate_limited_get(
                f"{VEDABASE_API}{next_page}"
            )
            verses.extend(verses_data.get("results", []))

        return verses

    async def get_verse_details(self, book_id: str, chapter_number: int, verse_number: int) -> dict:
        """Fetch full verse details including commentaries"""
        verse_data = await self._rate_limited_get(
            f"{VEDABASE_API}/books/{book_id}/chapters/{chapter_number}/verses/{verse_number}/?language=en"
        )
        return verse_data

    async def scrape_all_books(self):
        """Main scraping orchestration"""
        logger.info("=== VedaBase Comprehensive Scraper ===")
        logger.info(f"Output directory: {self.output_dir}")

        books = await self.get_all_books()

        all_data = {
            "metadata": {
                "source": "vedabase.io",
                "scraped_at": datetime.now().isoformat(),
                "total_books": len(books),
            },
            "books": {},
        }

        for idx, book in enumerate(books, 1):
            book_id = book.get("id")
            book_name = book.get("title", "Unknown")
            logger.info(f"\n[{idx}/{len(books)}] Processing: {book_name}")

            chapters = await self.get_book_chapters(book_id)
            logger.info(f"  Found {len(chapters)} chapters")

            book_data = {
                "id": book_id,
                "title": book_name,
                "description": book.get("description", ""),
                "author": book.get("author_name", ""),
                "cover_url": book.get("cover_image", ""),
                "chapters": {},
            }

            for chapter_idx, chapter in enumerate(chapters, 1):
                chapter_number = chapter.get("chapter_number")
                chapter_title = chapter.get("name", f"Chapter {chapter_number}")
                logger.info(f"    Chapter {chapter_number}/{len(chapters)}: {chapter_title}")

                verses = await self.get_chapter_verses(book_id, chapter_number)

                chapter_data = {
                    "chapter_number": chapter_number,
                    "title": chapter_title,
                    "verses": {},
                }

                for verse in verses:
                    verse_number = verse.get("verse_number")

                    # Get full details with commentaries
                    verse_details = await self.get_verse_details(
                        book_id, chapter_number, verse_number
                    )

                    verse_data = {
                        "verse_number": verse_number,
                        "text": verse_details.get("text", ""),
                        "devanagari": verse_details.get("devanagari_text", ""),
                        "transliteration": verse_details.get("transliteration", ""),
                        "translation": verse_details.get("translation", ""),
                        "word_meanings": verse_details.get("word_meanings", []),
                        "purports": verse_details.get("purports", []),  # Commentaries
                        "synonyms": verse_details.get("synonyms", ""),
                    }

                    chapter_data["verses"][verse_number] = verse_data

                book_data["chapters"][chapter_number] = chapter_data

            all_data["books"][book_id] = book_data

            # Save incrementally to avoid data loss
            self._save_progress(all_data)

        logger.info("\n=== Scraping Complete ===")
        logger.info(f"Total requests: {self.request_count}")
        self._save_final_data(all_data)
        return all_data

    def _save_progress(self, data: dict):
        """Save progress incrementally"""
        output_file = self.output_dir / "vedabase_data.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _save_final_data(self, data: dict):
        """Save final data and generate summary"""
        self._save_progress(data)

        # Generate summary
        summary = {
            "scraped_at": data["metadata"]["scraped_at"],
            "total_books": len(data["books"]),
            "books": {},
        }

        for book_id, book in data["books"].items():
            verse_count = sum(len(ch.get("verses", {})) for ch in book.get("chapters", {}).values())
            summary["books"][book_id] = {
                "title": book.get("title"),
                "chapters": len(book.get("chapters", {})),
                "verses": verse_count,
            }

        summary_file = self.output_dir / "scrape_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        logger.info(f"\nSummary saved to {summary_file}")


async def main():
    async with VedaBaseScraper() as scraper:
        await scraper.scrape_all_books()


if __name__ == "__main__":
    asyncio.run(main())
