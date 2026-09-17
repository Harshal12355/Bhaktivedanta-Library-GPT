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

        # Merge verses with cross-references
        merged = {}
        merged_count = 0

        for verse_key, pdf_verse in pdf_verses.items():
            chapter = pdf_verse.get("chapter")
            verse_num = pdf_verse.get("verse")

            merged[verse_key] = {
                "reference": f"BG {chapter}.{verse_num}",
                "chapter": chapter,
                "verse": verse_num,
                "sources": {
                    "pdf": pdf_verse.get("text", ""),
                },
                "concepts": [],
            }
            merged_count += 1

        # Add VedaBase data if available
        for book_id, book in vedabase_data.get("books", {}).items():
            for chapter_num, chapter in book.get("chapters", {}).items():
                for verse_num, verse in chapter.get("verses", {}).items():
                    # Try to match with BG
                    if book_id == "bhagavad-gita":
                        key = f"{chapter_num}.{verse_num}"
                        if key in merged:
                            merged[key]["sources"]["vedabase"] = verse.get("translation")

        self.pipeline_data["merged_verses"] = merged

        # Validation report
        validation = {
            "total_pdf_verses": len(pdf_verses),
            "total_vedabase_books": len(vedabase_data.get("books", {})),
            "total_concepts": len(concepts),
            "merged_verses": merged_count,
            "checks": {
                "all_pdf_verses_merged": merged_count == len(pdf_verses),
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
