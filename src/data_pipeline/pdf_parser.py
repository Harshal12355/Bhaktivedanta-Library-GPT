"""
PDF Parser for Bhagavad Gita
Extracts verses, chapter structure, and text from PDF files
"""

import json
import re
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import logging

# Try common PDF libraries
try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("./data/pdf_extracted")


class BhagavadGitaPDFParser:
    """Parse Bhagavad Gita PDF and extract verses with structure"""

    def __init__(self, pdf_path: Path = None):
        self.pdf_path = pdf_path or Path("./data/Bhagavad-Gita As It Is.pdf")
        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")

        self.verses_data = {}
        self.library = None

        # Detect available library
        if HAS_PDFPLUMBER:
            self.library = "pdfplumber"
        elif HAS_PYPDF2:
            self.library = "PyPDF2"
        else:
            raise ImportError("Install pdfplumber or PyPDF2: pip install pdfplumber")

        logger.info(f"Using {self.library} for PDF parsing")

    def parse_with_pdfplumber(self) -> Dict:
        """Parse using pdfplumber (recommended)"""
        import pdfplumber

        verses = {}

        with pdfplumber.open(self.pdf_path) as pdf:
            logger.info(f"PDF has {len(pdf.pages)} pages")

            current_chapter = None
            current_verse = None
            current_text = []

            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue

                lines = text.split("\n")

                for line in lines:
                    line = line.strip()

                    # Detect chapter headers (e.g., "CHAPTER 1" or "Chapter 1:")
                    chapter_match = re.match(r"[Cc]hapter\s+(\d+)", line)
                    if chapter_match:
                        current_chapter = int(chapter_match.group(1))
                        logger.info(f"Found Chapter {current_chapter}")
                        continue

                    # Detect verse markers (e.g., "1.1" or "Verse 1")
                    verse_match = re.match(r"(\d+)[.\-](\d+)", line)
                    if verse_match and current_chapter:
                        # Save previous verse if exists
                        if current_verse and current_text:
                            key = f"{current_chapter}.{current_verse}"
                            verses[key] = {
                                "chapter": current_chapter,
                                "verse": current_verse,
                                "text": " ".join(current_text).strip(),
                                "source": "PDF",
                            }

                        current_verse = int(verse_match.group(2))
                        current_text = []
                        logger.debug(f"Found Verse {current_chapter}.{current_verse}")
                        continue

                    # Accumulate verse text
                    if current_verse and line:
                        current_text.append(line)

            # Save last verse
            if current_verse and current_text:
                key = f"{current_chapter}.{current_verse}"
                verses[key] = {
                    "chapter": current_chapter,
                    "verse": current_verse,
                    "text": " ".join(current_text).strip(),
                    "source": "PDF",
                }

        return verses

    def parse_with_pypdf2(self) -> Dict:
        """Fallback parser using PyPDF2"""
        import PyPDF2

        verses = {}

        with open(self.pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            logger.info(f"PDF has {len(reader.pages)} pages")

            full_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

            # Use same regex-based extraction as pdfplumber version
            lines = full_text.split("\n")
            current_chapter = None
            current_verse = None
            current_text = []

            for line in lines:
                line = line.strip()

                chapter_match = re.match(r"[Cc]hapter\s+(\d+)", line)
                if chapter_match:
                    current_chapter = int(chapter_match.group(1))
                    continue

                verse_match = re.match(r"(\d+)[.\-](\d+)", line)
                if verse_match and current_chapter:
                    if current_verse and current_text:
                        key = f"{current_chapter}.{current_verse}"
                        verses[key] = {
                            "chapter": current_chapter,
                            "verse": current_verse,
                            "text": " ".join(current_text).strip(),
                            "source": "PDF",
                        }

                    current_verse = int(verse_match.group(2))
                    current_text = []
                    continue

                if current_verse and line:
                    current_text.append(line)

            if current_verse and current_text:
                key = f"{current_chapter}.{current_verse}"
                verses[key] = {
                    "chapter": current_chapter,
                    "verse": current_verse,
                    "text": " ".join(current_text).strip(),
                    "source": "PDF",
                }

        return verses

    def parse(self) -> Dict:
        """Parse PDF and extract verses"""
        logger.info(f"Parsing {self.pdf_path}...")

        if self.library == "pdfplumber":
            verses = self.parse_with_pdfplumber()
        else:
            verses = self.parse_with_pypdf2()

        logger.info(f"Extracted {len(verses)} verses from PDF")
        self.verses_data = verses
        return verses

    def save_json(self):
        """Save extracted verses to JSON"""
        output_file = self.output_dir / "bhagavad_gita_pdf.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.verses_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved to {output_file}")

    def get_statistics(self) -> Dict:
        """Get parsing statistics"""
        if not self.verses_data:
            return {}

        chapters = set(v["chapter"] for v in self.verses_data.values())
        return {
            "total_verses": len(self.verses_data),
            "chapters": sorted(chapters),
            "verses_per_chapter": {
                ch: len([v for v in self.verses_data.values() if v["chapter"] == ch])
                for ch in sorted(chapters)
            },
        }


def main():
    parser = BhagavadGitaPDFParser()
    verses = parser.parse()
    parser.save_json()

    stats = parser.get_statistics()
    logger.info(f"\nStatistics: {json.dumps(stats, indent=2)}")


if __name__ == "__main__":
    main()
