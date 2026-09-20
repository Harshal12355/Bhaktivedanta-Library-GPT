"""
Data Collection Pipeline Orchestrator
Runs all scrapers and parsers in sequence, validates, and merges data
"""

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_pipeline.pdf_parser import BhagavadGitaPDFParser
from data_pipeline.vedabase_scraper import VedaBaseScraper
from data_pipeline.vanipedia_scraper import VanipediaScraper


class DataCollectionPipeline:
    """Orchestrate all data collection and merging"""

    def __init__(self, output_base: Path = Path("./data/pipeline_output")):
        self.output_base = output_base
        self.output_base.mkdir(parents=True, exist_ok=True)
        self.pipeline_data = {
            "metadata": {
                "started_at": datetime.now().isoformat(),
                "status": "running",
            },
            "pdf_verses": {},
            "vedabase_books": {},
            "vanipedia_concepts": {},
            "merged_verses": {},
            "validation_report": {},
        }

    async def run_full_pipeline(self):
        """Execute all data collection steps"""
        logger.info("=" * 60)
        logger.info("STARTING FULL DATA COLLECTION PIPELINE")
        logger.info("=" * 60)

        try:
            # Step 1: Parse PDF
            logger.info("\n[STEP 1/3] Parsing Bhagavad Gita PDFs...")
            self.pipeline_data["pdf_verses"] = self._run_pdf_parser()

            # Step 2: Scrape VedaBase
            logger.info("\n[STEP 2/3] Scraping VedaBase (all English books)...")
            self.pipeline_data["vedabase_books"] = await self._run_vedabase_scraper()

            # Step 3: Scrape Vanipedia
            logger.info("\n[STEP 3/3] Scraping Vanipedia concepts...")
            self.pipeline_data["vanipedia_concepts"] = await self._run_vanipedia_scraper()

            # Step 4: Merge and validate
            logger.info("\n[STEP 4/4] Merging and validating data...")
            self._merge_and_validate()

            # Final save
            self._save_pipeline_data()

            logger.info("\n" + "=" * 60)
            logger.info("PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            self.pipeline_data["metadata"]["status"] = "failed"
            self.pipeline_data["metadata"]["error"] = str(e)
            self._save_pipeline_data()
            raise

    def _run_pdf_parser(self) -> Dict:
        """Run PDF parser"""
        try:
            parser = BhagavadGitaPDFParser()
            verses = parser.parse()
            parser.save_json()

            stats = parser.get_statistics()
            logger.info(f"PDF Statistics: {stats}")

            return {
                "status": "success",
                "verses_count": len(verses),
                "statistics": stats,
                "verses": verses,
            }
        except Exception as e:
            logger.error(f"PDF parsing failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
            }

    async def _run_vedabase_scraper(self) -> Dict:
        """Run VedaBase scraper"""
        try:
            async with VedaBaseScraper() as scraper:
                data = await scraper.scrape_all_books()

            # Count books and verses
            total_verses = sum(
                sum(len(ch.get("verses", {})) for ch in book.get("chapters", {}).values())
                for book in data.get("books", {}).values()
            )

            return {
                "status": "success",
                "books_count": len(data.get("books", {})),
                "verses_count": total_verses,
                "data": data,
            }
        except Exception as e:
            logger.error(f"VedaBase scraping failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
            }

    async def _run_vanipedia_scraper(self) -> Dict:
        """Run Vanipedia scraper"""
        try:
            async with VanipediaScraper() as scraper:
                concepts = await scraper.scrape_key_concepts()

            return {
                "status": "success",
                "concepts_count": len(concepts),
                "concepts": concepts,
            }
        except Exception as e:
            logger.error(f"Vanipedia scraping failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
            }

    def _merge_and_validate(self):
        """Merge data sources and validate consistency"""
        logger.info("Merging data sources...")

        pdf_verses = self.pipeline_data["pdf_verses"].get("verses", {})
        vedabase_data = self.pipeline_data["vedabase_books"].get("data", {})
        concepts = self.pipeline_data["vanipedia_concepts"].get("concepts", {})

        # VedaBase is the corpus, not a supplement: it carries every book, and
        # the PDF covers only a handful of Bhagavad-gita verses, attached below
        # where it overlaps. Keying on the scraper's reference ("BG 1.1",
        # "SB 1.2.19") is what makes every book addressable - a bare
        # chapter.verse key collides across books and cannot express
        # Srimad-Bhagavatam's canto or Caitanya-caritamrta's lila level.
        merged = {}
        for book_id, book in vedabase_data.get("books", {}).items():
            for chapter_key, chapter in book.get("chapters", {}).items():
                for verse_num, verse in chapter.get("verses", {}).items():
                    reference = verse.get("reference")
                    if not reference:
                        continue
                    merged[reference] = {
                        "reference": reference,
                        "book": book_id,
                        "book_title": book.get("title", ""),
                        "chapter": chapter_key,
                        "verse": verse_num,
                        "url": verse.get("url", ""),
                        # Keyed by content type rather than by provenance,
                        # because the vault generator and the Phase B loader
                        # both read sources["translation"].
                        "sources": {
                            "devanagari": verse.get("devanagari", ""),
                            "transliteration": verse.get("transliteration", ""),
                            "synonyms": verse.get("synonyms", ""),
                            "translation": verse.get("translation", ""),
                            "purport": verse.get("purport", ""),
                        },
                        "concepts": [],
                    }

        # The PDF extract keys a verse "BG-1.1" where the scraper renders the
        # same verse "BG 1.1".
        pdf_attached = 0
        for pdf_key, pdf_verse in pdf_verses.items():
            entry = merged.get(pdf_key.replace("-", " ", 1))
            if entry is None:
                continue
            entry["sources"]["pdf"] = pdf_verse.get("text", "")
            pdf_attached += 1

        self.pipeline_data["merged_verses"] = merged

        with_translation = sum(1 for e in merged.values() if e["sources"]["translation"])

        # Validation report
        validation = {
            "total_merged_verses": len(merged),
            "books_merged": len({e["book"] for e in merged.values()}),
            "verses_with_translation": with_translation,
            "verses_with_purport": sum(1 for e in merged.values() if e["sources"]["purport"]),
            "pdf_verses_attached": pdf_attached,
            "pdf_verses_unmatched": len(pdf_verses) - pdf_attached,
            "total_concepts": len(concepts),
            "checks": {
                "vedabase_verses_merged": len(merged) > 0,
                "every_verse_has_translation": with_translation == len(merged),
                "concepts_extracted": len(concepts) > 0,
            },
        }

        self.pipeline_data["validation_report"] = validation
        logger.info(f"Validation Report: {json.dumps(validation, indent=2)}")

    def _save_pipeline_data(self):
        """Save all pipeline data to files"""
        # Main output
        output_file = self.output_base / "pipeline_complete.json"
        with open(output_file, "w", encoding="utf-8") as f:
            # Don't include raw data in main output (too large)
            summary = {
                "metadata": self.pipeline_data["metadata"],
                "pdf_summary": {
                    "status": self.pipeline_data["pdf_verses"].get("status"),
                    "verses_count": self.pipeline_data["pdf_verses"].get("verses_count"),
                    "statistics": self.pipeline_data["pdf_verses"].get("statistics"),
                },
                "vedabase_summary": {
                    "status": self.pipeline_data["vedabase_books"].get("status"),
                    "books_count": self.pipeline_data["vedabase_books"].get("books_count"),
                    "verses_count": self.pipeline_data["vedabase_books"].get("verses_count"),
                },
                "vanipedia_summary": {
                    "status": self.pipeline_data["vanipedia_concepts"].get("status"),
                    "concepts_count": self.pipeline_data["vanipedia_concepts"].get("concepts_count"),
                },
                "validation_report": self.pipeline_data["validation_report"],
            }
            json.dump(summary, f, indent=2)

        logger.info(f"Saved pipeline summary to {output_file}")

        # Save merged verses
        if self.pipeline_data["merged_verses"]:
            merged_file = self.output_base / "merged_verses.json"
            with open(merged_file, "w", encoding="utf-8") as f:
                json.dump(self.pipeline_data["merged_verses"], f, ensure_ascii=False, indent=2)
            logger.info(f"Saved merged verses to {merged_file}")

        # Save concepts
        if self.pipeline_data["vanipedia_concepts"].get("concepts"):
            concepts_file = self.output_base / "concepts.json"
            with open(concepts_file, "w", encoding="utf-8") as f:
                json.dump(
                    self.pipeline_data["vanipedia_concepts"]["concepts"],
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
            logger.info(f"Saved concepts to {concepts_file}")

        # Summary stats
        self.pipeline_data["metadata"]["completed_at"] = datetime.now().isoformat()
        self.pipeline_data["metadata"]["status"] = "completed"


async def main():
    pipeline = DataCollectionPipeline()
    await pipeline.run_full_pipeline()


if __name__ == "__main__":
    asyncio.run(main())
