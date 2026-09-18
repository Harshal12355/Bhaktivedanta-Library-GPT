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

# Chapter pages expose an "advanced-view" rendering holding every verse at once.
ADVANCED_VIEW = "advanced-view"
# book -> canto/lila -> chapter is the deepest the library nests.
MAX_NESTING_DEPTH = 3
MAX_RETRIES = 4
RETRY_BACKOFF_SECONDS = 2


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
        """Rate-limited GET. Returns None only for 404 - the path is not there.

        Transient failures are retried and then allowed to propagate. Reporting
        them as an empty page would be indistinguishable from a page that really
        holds nothing, and callers would record a book as having no chapters:
        a dropped connection would quietly yield a corpus that looks complete
        and is empty.
        """
        url = f"{VEDABASE_BASE}{path}"
        for attempt in range(MAX_RETRIES):
            elapsed = time.time() - self.last_request_time
            if elapsed < RATE_LIMIT_DELAY:
                await asyncio.sleep(RATE_LIMIT_DELAY - elapsed)

            self.request_count += 1
            if self.request_count % 10 == 0:
                logger.info(f"Requests made: {self.request_count}")

            try:
                response = await self.session.get(url)
                self.last_request_time = time.time()
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return BeautifulSoup(response.text, "lxml")
            except httpx.HTTPError as e:
                self.last_request_time = time.time()
                if attempt == MAX_RETRIES - 1:
                    logger.error(f"Giving up on {url} after {MAX_RETRIES} attempts: {e}")
                    raise
                backoff = RETRY_BACKOFF_SECONDS * (2 ** attempt)
                logger.warning(f"Error fetching {url}: {e} - retrying in {backoff}s")
                await asyncio.sleep(backoff)

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

    async def _list_children(self, path: str) -> list:
        """Return [(child_path, title)] one level below a library path."""
        soup = await self._rate_limited_get(path)
        if not soup:
            return []

        children = []
        seen = set()
        pattern = re.compile(rf"^{re.escape(path)}([\w-]+)/$")
        for a in soup.select(f'a[href^="{path}"]'):
            href = a.get("href", "")
            if href in seen:
                continue
            m = pattern.match(href)
            if not m:
                continue
            seen.add(href)
            children.append((href, a.get_text(" ", strip=True) or m.group(1)))
        return children

    async def fetch_chapter(self, chapter_path: str) -> list:
        """Fetch every verse of a chapter in a single request.

        The advanced-view page renders the whole chapter, so this costs one
        request rather than one per verse - for Srimad-Bhagavatam the difference
        between roughly an hour and a day and a half.
        """
        soup = await self._rate_limited_get(f"{chapter_path}{ADVANCED_VIEW}/")
        if not soup:
            return []
        container = soup.select_one(".av-verses")
        if not container:
            return []

        def text_of(block, css_class: str) -> str:
            el = block.select_one(f".{css_class}")
            if not el:
                return ""
            # Each field is prefixed by its own heading ("Translation", "Purport"),
            # which would otherwise be extracted as part of the field's text.
            for heading in el.select("h2, h3"):
                heading.extract()
            return el.get_text(" ", strip=True)

        # Matching only a single trailing segment is what keeps a canto from being
        # swallowed whole: /sb/1/advanced-view/ also renders verses, but theirs link
        # to /sb/1/<chapter>/<verse>/, so none match here and the walk descends
        # to the chapters instead of storing the canto as one giant chapter.
        pattern = re.compile(rf"^{re.escape(chapter_path)}([\w-]+)/$")
        verses = []
        for block in container.find_all("div", recursive=False):
            verse_number = None
            for a in block.select(f'a[href^="{chapter_path}"]'):
                m = pattern.match(a.get("href", ""))
                if m:
                    verse_number = m.group(1)
                    break
            if not verse_number:
                continue
            verses.append(
                {
                    "verse_number": verse_number,
                    "url": f"{VEDABASE_BASE}{chapter_path}{verse_number}/",
                    "devanagari": text_of(block, "av-devanagari"),
                    "transliteration": text_of(block, "av-verse_text"),
                    "synonyms": text_of(block, "av-synonyms"),
                    "translation": text_of(block, "av-translation"),
                    "purport": text_of(block, "av-purport"),
                }
            )
        return verses

    async def _scrape_node(self, path, title, book_data, prefix_len, all_data, depth=0):
        """Scrape a chapter, or recurse into a container of chapters.

        Whether a path holds verses is settled by asking for its advanced-view,
        not by assuming a nesting depth. Bhagavad-gita is book/chapter,
        Srimad-Bhagavatam inserts a canto, Caitanya-caritamrta a named lila
        (adi, madhya, antya), Sri Isopanisad has no chapter level at all, and
        several books open with front matter that is not a chapter. Asking is
        also self-correcting: a chapter answers with its verses in the same
        request, so the check costs nothing on the common path.
        """
        chapter_key = path[prefix_len:].strip("/") or "1"
        existing = book_data["chapters"].get(chapter_key)
        if existing and existing.get("complete"):
            return 0

        verses = await self.fetch_chapter(path)
        if verses:
            reference_base = f"{book_data['id'].upper()} {chapter_key.replace('/', '.')}"
            book_data["chapters"][chapter_key] = {
                "chapter_key": chapter_key,
                "title": title,
                "complete": True,
                "verses": {
                    verse["verse_number"]: {
                        "reference": f"{reference_base}.{verse['verse_number']}",
                        **verse,
                    }
                    for verse in verses
                },
            }
            self._save_progress(all_data)
            logger.info(f"    {chapter_key}: {title[:58]} ({len(verses)} verses)")
            return 1

        if depth >= MAX_NESTING_DEPTH:
            return 0

        scraped = 0
        for child_path, child_title in await self._list_children(path):
            scraped += await self._scrape_node(
                child_path, child_title, book_data, prefix_len, all_data, depth + 1
            )
        return scraped

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

            book_data = all_data["books"].setdefault(
                book_id, {"id": book_id, "title": book_name, "chapters": {}}
            )
            root = f"{LIBRARY_PATH}{book_id}/"
            scraped = await self._scrape_node(root, book_name, book_data, len(root), all_data)
            logger.info(
                f"  {scraped} chapter(s) scraped this run, "
                f"{len(book_data['chapters'])} held in total"
            )

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
