"""
Obsidian Vault Generator
Transforms Phase 0 merged data into Obsidian vault structure
Creates markdown files with YAML frontmatter and wikilinks
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ObsidianVaultGenerator:
    """Generate Obsidian vault from verse and concept data"""

    def __init__(self, vault_path: Path = Path("./vedic-vault")):
        self.vault_path = vault_path
        self.verses: Dict = {}
        self.concepts: Dict = {}

        # Create vault structure
        self.folders = {
            "root": self.vault_path,
            "vedic_texts": self.vault_path / "Vedic-Texts",
            "bhagavad_gita": self.vault_path / "Vedic-Texts" / "Bhagavad-Gita",
            "concepts": self.vault_path / "Concepts",
            "themes": self.vault_path / "Themes",
            "index": self.vault_path / "Index",
        }

    def setup_vault_structure(self):
        """Create vault folder structure"""
        logger.info(f"Setting up vault at {self.vault_path}")

        for folder in self.folders.values():
            folder.mkdir(parents=True, exist_ok=True)

        logger.info("✓ Vault structure created")

    def load_phase0_data(self):
        """Load merged verses and concepts from Phase 0"""
        verses_file = Path("./data/pipeline_output/merged_verses.json")
        concepts_file = Path("./data/pipeline_output/concepts.json")

        if verses_file.exists():
            with open(verses_file, "r", encoding="utf-8") as f:
                self.verses = json.load(f)
            logger.info(f"✓ Loaded {len(self.verses)} verses")
        else:
            logger.warning(f"Verses file not found: {verses_file}")

        if concepts_file.exists():
            with open(concepts_file, "r", encoding="utf-8") as f:
                self.concepts = json.load(f)
            logger.info(f"✓ Loaded {len(self.concepts)} concepts")
        else:
            logger.warning(f"Concepts file not found: {concepts_file}")

    def generate_verse_note(self, reference: str, verse_data: Dict) -> str:
        """Generate markdown for a single verse"""
        chapter = verse_data.get("chapter", "")
        verse_num = verse_data.get("verse", "")
        sources = verse_data.get("sources", {})
        concepts = verse_data.get("concepts", [])

        # YAML frontmatter
        frontmatter = f"""---
source_text: "Bhagavad Gita"
chapter: {chapter}
verse: {verse_num}
reference: "{reference}"
themes: {json.dumps(concepts)}
tags: [bhagavad-gita, verse]
copyright: "© ISKCON (Prabhupada)"
verified: true
confidence: "high"
created: {datetime.now().isoformat()}
---

"""

        # Content
        content = f"# {reference}\n\n"

        if sources.get("pdf"):
            content += f"## Sanskrit\n\n{sources['pdf']}\n\n"

        if sources.get("translation"):
            content += f"## Translation\n\n{sources['translation']}\n\n"

        if concepts:
            content += "## Related Concepts\n\n"
            for concept in concepts:
                content += f"- [[{concept}]]\n"
            content += "\n"

        content += f"## References\n\n"
        content += f"- [[Bhagavad-Gita]]\n"
        content += f"- [[Chapter {chapter}]]\n"

        return frontmatter + content

    def generate_concept_note(self, concept_name: str, concept_data: Dict) -> str:
        """Generate markdown for a concept"""
        title = concept_data.get("title", concept_name)
        definition = concept_data.get("definition", "")
        synonyms = concept_data.get("synonyms", [])
        related = concept_data.get("related_concepts", [])

        frontmatter = f"""---
concept: "{title}"
definition: "{definition}"
synonyms: {json.dumps(synonyms)}
related: {json.dumps(related)}
tags: [concept, vedic]
created: {datetime.now().isoformat()}
---

"""

        content = f"# {title}\n\n"

        if definition:
            content += f"> {definition}\n\n"

        if synonyms:
            content += "## Synonyms\n\n"
            content += ", ".join(f"*{s}*" for s in synonyms) + "\n\n"

        if related:
            content += "## Related Concepts\n\n"
            for rel in related:
                content += f"- [[{rel}]]\n"
            content += "\n"

        content += "## Verses\n\n"
        # Find verses mentioning this concept
        for verse_ref, verse_data in self.verses.items():
            if concept_name in verse_data.get("concepts", []):
                content += f"- [[{verse_ref}]]\n"

        return frontmatter + content

    def generate_chapter_note(self, chapter_num: int) -> str:
        """Generate markdown for a chapter"""
        verses_in_chapter = {
            ref: data for ref, data in self.verses.items()
            if data.get("chapter") == chapter_num
        }

        frontmatter = f"""---
chapter: {chapter_num}
source_text: "Bhagavad Gita"
verses: {len(verses_in_chapter)}
tags: [chapter, bhagavad-gita]
created: {datetime.now().isoformat()}
---

"""

        content = f"# Chapter {chapter_num}\n\n"
        content += f"## Verses ({len(verses_in_chapter)})\n\n"

        for verse_ref in sorted(verses_in_chapter.keys()):
            content += f"- [[{verse_ref}]]\n"

        content += "\n## Overview\n\nChapter summary and key teachings would go here.\n"

        return frontmatter + content

    def generate_theme_note(self, theme: str, verses: List[str]) -> str:
        """Generate markdown for a thematic grouping"""
        frontmatter = f"""---
theme: "{theme}"
verses: {len(verses)}
tags: [theme]
created: {datetime.now().isoformat()}
---

"""

        content = f"# {theme}\n\n"
        content += f"Verses exploring {theme}:\n\n"

        for verse_ref in verses:
            content += f"- [[{verse_ref}]]\n"

        return frontmatter + content

    def write_verses(self):
        """Write verse notes to vault"""
        logger.info("Writing verse notes...")

        # Group by chapter
        by_chapter = {}
        for ref, data in self.verses.items():
            chapter = data.get("chapter")
            if chapter not in by_chapter:
                by_chapter[chapter] = {}
            by_chapter[chapter][ref] = data

        # Create chapter folders and verse notes
        for chapter, verses in sorted(by_chapter.items()):
            chapter_folder = self.folders["bhagavad_gita"] / f"Chapter-{chapter}"
            chapter_folder.mkdir(exist_ok=True)

            # Write chapter index
            chapter_note = self.generate_chapter_note(chapter)
            chapter_file = chapter_folder / "_index.md"
            chapter_file.write_text(chapter_note, encoding="utf-8")

            # Write individual verses
            for ref, data in verses.items():
                verse_note = self.generate_verse_note(ref, data)
                verse_file = chapter_folder / f"{ref.replace(' ', '-')}.md"
                verse_file.write_text(verse_note, encoding="utf-8")

        logger.info(f"✓ Wrote {len(self.verses)} verse notes")

    def write_concepts(self):
        """Write concept notes to vault"""
        logger.info("Writing concept notes...")

        for concept_name, concept_data in self.concepts.items():
            concept_note = self.generate_concept_note(concept_name, concept_data)
            concept_file = self.folders["concepts"] / f"{concept_name}.md"
            concept_file.write_text(concept_note, encoding="utf-8")

        logger.info(f"✓ Wrote {len(self.concepts)} concept notes")

    def write_index(self):
        """Write vault index"""
        logger.info("Writing vault index...")

        index_content = f"""---
title: "Vedic Knowledge Vault"
type: "index"
created: {datetime.now().isoformat()}
---

# Vedic Knowledge Vault

A comprehensive, interconnected knowledge base of Vedic philosophy and texts.

## 📚 Vedic Texts

- [[Bhagavad-Gita]] - The Song of God (18 chapters, {len(self.verses)} verses)

## 🔮 Core Concepts

### Spiritual Principles
"""

        # Group concepts by theme
        concept_list = sorted(self.concepts.keys())
        for concept in concept_list:
            index_content += f"- [[{concept}]]\n"

        index_content += f"""

## 📖 How to Use

1. **Browse by Text** - Start in Vedic-Texts folder
2. **Explore Concepts** - Jump to Concepts for philosophical topics
3. **Search** - Use Obsidian search (Cmd/Ctrl+F) to find verses
4. **Link Navigation** - Click any [[ ]] link to jump between notes

## 📊 Vault Stats

- **Total Verses**: {len(self.verses)}
- **Total Concepts**: {len(self.concepts)}
- **Books**: 1 (Bhagavad Gita)
- **Last Updated**: {datetime.now().isoformat()}

## 🔗 Cross-References

All verses link to related concepts, and concepts link back to verses mentioning them.

---

*This vault was generated from Phase 0 data collection pipeline.*
"""

        index_file = self.folders["root"] / "INDEX.md"
        index_file.write_text(index_content, encoding="utf-8")
        logger.info("✓ Vault index created")

    def write_vault_settings(self):
        """Write .obsidian settings for vault"""
        obsidian_dir = self.vault_path / ".obsidian"
        obsidian_dir.mkdir(exist_ok=True)

        # Core settings
        settings = {
            "pluginEnabledStatus": {},
            "fileTreeDisplayNameFormat": "fileNameAndFolderPathExceptRoot"
        }

        settings_file = obsidian_dir / "app.json"
        settings_file.write_text(json.dumps(settings, indent=2), encoding="utf-8")

        # Workspace settings
        workspace = {
            "main": {
                "file": "INDEX.md",
                "leaf": 0
            }
        }

        workspace_file = obsidian_dir / "workspace.json"
        workspace_file.write_text(json.dumps(workspace, indent=2), encoding="utf-8")

        logger.info("✓ Obsidian settings created")

    def generate_vault(self):
        """Run full vault generation pipeline"""
        logger.info("=" * 60)
        logger.info("PHASE A: OBSIDIAN VAULT GENERATION")
        logger.info("=" * 60)

        self.setup_vault_structure()
        self.load_phase0_data()

        if not self.verses or not self.concepts:
            logger.error("No data loaded from Phase 0. Run Phase 0 first.")
            return False

        self.write_verses()
        self.write_concepts()
        self.write_index()
        self.write_vault_settings()

        logger.info("=" * 60)
        logger.info("✓ VAULT GENERATED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info(f"\nVault location: {self.vault_path}")
        logger.info(f"\nTo open in Obsidian:")
        logger.info(f"  1. Open Obsidian")
        logger.info(f"  2. 'Open vault' → Select: {self.vault_path}")
        logger.info(f"  3. Start at INDEX.md")

        return True


def main():
    generator = ObsidianVaultGenerator()
    generator.generate_vault()


if __name__ == "__main__":
    main()
