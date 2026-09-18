"""
VedaBase Comprehensive Scraper
Fetches all English books, chapters, verses, and commentaries from vedabase.io

NOTE: vedabase.io no longer exposes the /api/books/... REST API used by the
original version of this scraper (it now returns 404 - the site was rebuilt
on Next.js). This version scrapes the rendered HTML pages under
https://vedabase.io/en/library/ instead, which robots.txt explicitly allows
(Allow: /) subject to a 10-second crawl delay, which is honored by default
below.
"""

import argparse
import asyncio
import json
import os
import re
import time
from typing import Optional
from pathlib import Path
import httpx
from bs4 import BeautifulSoup
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VEDABASE_BASE = "https://vedabase.io"
LIBRARY_PATH = "/en/library/"
# robots.txt on vedabase.io specifies "Crawl-delay: 10" - respected by default.
RATE_LIMIT_DELAY = float(os.environ.get("VEDABASE_RATE_LIMIT", "10.0"))
OUTPUT_DIR = Path("./data/vedabase_raw")
USER_AGENT = "BhaktivedantaLibraryGPT-Research/1.0 (+personal study/RAG project)"

CHAPTER_LINK_RE = re.compile(r"^/en/library/([a-z0-9\-]+)/(\d+)/$")


class VedaBaseScraper:
    def __init__(self, output_dir: Path = OUTPUT_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session: Optional[httpx.AsyncClient] = None
        self.request_count = 0
        self.last_request_time = 0

    async def __aenter__(self):
        self.session = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, *args):
        await self.session.aclose()

    async def _rate_limited_get(self, path: str) -> Optional[BeautifulSoup]:
        """Rate-limited GET request, returns parsed HTML or None on failure"""
        elapsed = time.time() - self.last_request_time
        if elapsed < RATE_LIMIT_DELAY:
            await asyncio.sleep(RATE_LIMIT_DELAY - elapsed)

        self.request_count += 1
        if self.request_count % 10 == 0:
            logger.info(f"Requests made: {self.request_count}")

        url = f"{VEDABASE_BASE}{path}"
        try:
            response = await self.session.get(url)
            self.last_request_time = time.time()
            response.raise_for_status()
            return BeautifulSoup(response.text, "lxml")
        except httpx.HTTPError as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    async def get_all_books(self) -> list:
        """Fetch all books listed in the English library index"""
        logger.info("Fetching all English books...")
        soup = await self._rate_limited_get(LIBRARY_PATH)
        books = []
        if not soup:
            return books

        seen = set()
        for a in soup.select(f'a[href^="{LIBRARY_PATH}"]'):
            href = a.get("href", "")
            m = re.match(rf"^{LIBRARY_PATH}([a-z0-9\-]+)/$", href)
            if not m:
                continue
            slug = m.group(1)
            if slug in seen or slug in ("transcripts", "letters"):
                # Transcripts/Letters are huge non-verse collections; skip by default
                continue
            seen.add(slug)
            title = a.get_text(" ", strip=True) or slug
            books.append({"id": slug, "title": title})

        logger.info(f"Found {len(books)} English books")
        return books

    async def get_book_chapters(self, book_id: str) -> list:
        """Fetch all chapters for a book"""
        soup = await self._rate_limited_get(f"{LIBRARY_PATH}{book_id}/")
        chapters = []
        if not soup:
            return chapters

        seen = set()
        for a in soup.select(f'a[href^="{LIBRARY_PATH}{book_id}/"]'):
            href = a.get("href", "")
            m = CHAPTER_LINK_RE.match(href)
            if not m or m.group(1) != book_id:
                continue
            chapter_number = int(m.group(2))
            if chapter_number in seen:
                continue
            seen.add(chapter_number)
            title = a.get_text(" ", strip=True) or f"Chapter {chapter_number}"
            chapters.append({"chapter_number": chapter_number, "name": title})

        chapters.sort(key=lambda c: c["chapter_number"])
        return chapters

    async def get_chapter_verses(self, book_id: str, chapter_number: int) -> list:
        """Fetch all verse identifiers in a chapter (e.g. '1', '16-18')"""
        soup = await self._rate_limited_get(f"{LIBRARY_PATH}{book_id}/{chapter_number}/")
        verses = []
        if not soup:
            return verses

        prefix = f"{LIBRARY_PATH}{book_id}/{chapter_number}/"
        seen = set()
        for a in soup.select(f'a[href^="{prefix}"]'):
            href = a.get("href", "")
            m = re.match(rf"^{re.escape(prefix)}([\w]+(?:-[\w]+)?)/$", href)
            if not m:
                continue
            verse_number = m.group(1)
            if verse_number in seen:
                continue
            seen.add(verse_number)
            verses.append({"verse_number": verse_number})

        return verses

    async def get_verse_details(self, book_id: str, chapter_number: int, verse_number: str) -> dict:
        """Fetch full verse details including commentary, from the rendered page"""
        soup = await self._rate_limited_get(f"{LIBRARY_PATH}{book_id}/{chapter_number}/{verse_number}/")
        if not soup:
            return {}

        def text_of(css_class: str) -> str:
            el = soup.select_one(f".{css_class}")
            if not el:
                return ""
            # Drop the hidden section heading (e.g. "Translation") before extracting text
            heading = el.select_one("h2")
            if heading:
                heading.extract()
            return el.get_text(" ", strip=True)

        h1 = soup.select_one("h1")
        return {
            "reference": h1.get_text(" ", strip=True) if h1 else "",
            "devanagari": text_of("av-devanagari"),
            "transliteration": text_of("av-verse_text"),
            "synonyms": text_of("av-synonyms"),
            "translation": text_of("av-translation"),
            "purport": text_of("av-purport"),
        }

    def _load_existing(self) -> dict:
        """Load a previous (possibly partial) run so an interrupted scrape can resume"""
        output_file = self.output_dir / "vedabase_data.json"
        if not output_file.exists():
            return {}
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            existing_verses = sum(
                len(ch.get("verses", {}))
                for book in data.get("books", {}).values()
                for ch in book.get("chapters", {}).values()
            )
            logger.info(f"Resuming from existing output: {existing_verses} verses already scraped")
            return data
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Could not load existing output ({e}), starting fresh")
            return {}

    async def scrape_all_books(
        self,
        max_books: Optional[int] = None,
        max_chapters_per_book: Optional[int] = None,
        book_ids: Optional[list] = None,
    ):
        """Main scraping orchestration. Resumable: re-running skips verses already saved.

        book_ids restricts the run to those library slugs; the full corpus is
        tens of thousands of verses, so scoping it is often the difference
        between hours and days.
        """
        logger.info("=== VedaBase Comprehensive Scraper ===")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Rate limit: {RATE_LIMIT_DELAY}s between requests")

        books = await self.get_all_books()
        if book_ids:
            available = {b["id"] for b in books}
            unknown = [b for b in book_ids if b not in available]
            if unknown:
                raise ValueError(
                    f"Unknown book id(s): {', '.join(unknown)}. "
                    f"Available: {', '.join(sorted(available))}"
                )
            books = [b for b in books if b["id"] in book_ids]
            logger.info(f"Restricted to {len(books)} book(s): {', '.join(book_ids)}")
        if max_books:
            books = books[:max_books]

        existing = self._load_existing()
        all_data = {
            "metadata": {
                "source": "vedabase.io",
                "scraped_at": datetime.now().isoformat(),
                "total_books": len(books),
            },
            "books": existing.get("books", {}),
        }

        for idx, book in enumerate(books, 1):
            book_id = book.get("id")
            book_name = book.get("title", "Unknown")
            logger.info(f"\n[{idx}/{len(books)}] Processing: {book_name}")

            chapters = await self.get_book_chapters(book_id)
            if max_chapters_per_book:
                chapters = chapters[:max_chapters_per_book]
            logger.info(f"  Found {len(chapters)} chapters")

            book_data = all_data["books"].setdefault(
                book_id, {"id": book_id, "title": book_name, "chapters": {}}
            )

            for chapter in chapters:
                chapter_number = chapter.get("chapter_number")
                chapter_key = str(chapter_number)
                chapter_title = chapter.get("name", f"Chapter {chapter_number}")

                existing_chapter = book_data["chapters"].get(chapter_key)
                # A chapter marked complete is skipped without any HTTP request. Without
                # this flag every restart re-fetches each finished chapter's listing just
                # to count its verses - 335 wasted requests for Srimad-Bhagavatam alone.
                if existing_chapter and existing_chapter.get("complete"):
                    continue

                verses = await self.get_chapter_verses(book_id, chapter_number)
                already_done = (
                    existing_chapter is not None
                    and len(existing_chapter.get("verses", {})) >= len(verses)
                    and verses
                )
                if already_done:
                    logger.info(f"    Chapter {chapter_number}/{len(chapters)}: already scraped, marking complete")
                    existing_chapter["complete"] = True
                    self._save_progress(all_data)
                    continue

                logger.info(f"    Chapter {chapter_number}/{len(chapters)}: {chapter_title}")
                chapter_data = existing_chapter or {
                    "chapter_number": chapter_number,
                    "title": chapter_title,
                    "verses": {},
                }

                book_data["chapters"][chapter_key] = chapter_data

                for verse in verses:
                    verse_number = verse.get("verse_number")
                    if verse_number in chapter_data["verses"]:
                        continue  # already scraped in a previous run

                    verse_details = await self.get_verse_details(book_id, chapter_number, verse_number)
                    if not verse_details:
                        continue

                    chapter_data["verses"][verse_number] = {
                        "verse_number": verse_number,
                        **verse_details,
                    }
                    # Saving per verse (not per chapter) keeps an abrupt kill from
                    # discarding a whole chapter's worth of requests. The write costs
                    # far less than the crawl delay already spent on each verse.
                    self._save_progress(all_data)

                if verses and len(chapter_data["verses"]) >= len(verses):
                    chapter_data["complete"] = True
                self._save_progress(all_data)

        logger.info("\n=== Scraping Complete ===")
        logger.info(f"Total requests: {self.request_count}")
        self._save_final_data(all_data)
        return all_data

    def _save_progress(self, data: dict):
        """Save progress incrementally, atomically.

        Writing in place would leave a truncated, unparseable file if the process
        is killed mid-write, and _load_existing discards everything it cannot parse.
        """
        output_file = self.output_dir / "vedabase_data.json"
        tmp_file = output_file.with_suffix(".json.tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_file, output_file)

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
    parser = argparse.ArgumentParser(
        description=(
            "Scrape English books from vedabase.io. Resumable: re-running continues "
            "from whatever is already in the output file."
        )
    )
    parser.add_argument(
        "--books",
        metavar="IDS",
        help="Comma-separated book ids to scrape, e.g. 'bg,iso,noi'. Default: all.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available book ids and exit, without scraping.",
    )
    args = parser.parse_args()

    async with VedaBaseScraper() as scraper:
        if args.list:
            for book in await scraper.get_all_books():
                print(f"{book['id']:<16}{book['title']}")
            return

        book_ids = [b.strip() for b in args.books.split(",") if b.strip()] if args.books else None
        try:
            await scraper.scrape_all_books(book_ids=book_ids)
        except ValueError as e:
            raise SystemExit(str(e))


if __name__ == "__main__":
    asyncio.run(main())
