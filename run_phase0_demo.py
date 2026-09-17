#!/usr/bin/env python3
"""
Phase 0 Demo: Run data collection pipeline with mock/real data
Shows the full flow: PDF → VedaBase → Vanipedia → Merge
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data_pipeline.mock_data import generate_mock_pdf_data


async def run_demo():
    """Run Phase 0 demo with available data"""

    print("\n" + "="*60)
    print("PHASE 0 DEMO: Vedic Knowledge Data Collection")
    print("="*60)

    output_dir = Path("./data/pipeline_output")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Generate mock PDF data
    print("\n[STEP 1/3] Generating mock Bhagavad Gita data...")
    pdf_verses = generate_mock_pdf_data()

    # Step 2: Create mock VedaBase data
    print("\n[STEP 2/3] Generating mock VedaBase books...")
    vedabase_data = {
        "books": {
            "bhagavad-gita": {
                "id": "bhagavad-gita",
                "title": "Bhagavad Gita",
                "chapters": {
                    "1": {
                        "chapter_number": 1,
                        "title": "Yoga of Arjuna's Despair",
                        "verses": {
                            "1": {
                                "verse_number": 1,
                                "text": "Dharma-kṣetre kuru-kṣetre",
                                "translation": "On the holy field of Kurukṣetra...",
                                "purports": [
                                    {
                                        "author": "Prabhupada",
                                        "text": "This is the beginning of the narration..."
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }
    }
    print(f"✓ Generated mock VedaBase: 1 book")

    # Step 3: Create mock Vanipedia concepts
    print("\n[STEP 3/3] Generating mock Vanipedia concepts...")
    vanipedia_data = {
        "Dharma": {
            "id": "dharma",
            "title": "Dharma",
            "definition": "Religious duty; righteousness; cosmic law",
            "synonyms": ["duty", "righteousness", "law"],
            "related_concepts": ["Karma", "Yoga"]
        },
        "Bhakti": {
            "id": "bhakti",
            "title": "Bhakti",
            "definition": "Devotion; loving service to the Supreme Lord",
            "synonyms": ["devotion", "love", "service"],
            "related_concepts": ["Krishna", "Love"]
        },
        "Yoga": {
            "id": "yoga",
            "title": "Yoga",
            "definition": "Union; skill in action; spiritual discipline",
            "synonyms": ["union", "discipline"],
            "related_concepts": ["Meditation", "Action"]
        }
    }
    print(f"✓ Generated mock Vanipedia: {len(vanipedia_data)} concepts")

    # Step 4: Merge all data
    print("\n[STEP 4/4] Merging data sources...")
    merged_verses = {}
    for key, verse in pdf_verses.items():
        merged_verses[f"BG {key}"] = {
            "reference": f"BG {key}",
            "chapter": verse["chapter"],
            "verse": verse["verse"],
            "sources": {
                "pdf": verse["text"],
                "translation": verse["translation"]
            },
            "concepts": ["Dharma", "Yoga"]
        }

    # Step 5: Save merged data
    print("\n[STEP 5/5] Saving merged data...")

    # Save merged verses
    merged_file = output_dir / "merged_verses.json"
    with open(merged_file, "w", encoding="utf-8") as f:
        json.dump(merged_verses, f, ensure_ascii=False, indent=2)

    # Save concepts
    concepts_file = output_dir / "concepts.json"
    with open(concepts_file, "w", encoding="utf-8") as f:
        json.dump(vanipedia_data, f, ensure_ascii=False, indent=2)

    # Save summary
    summary = {
        "status": "success",
        "pdf_verses": len(pdf_verses),
        "vedabase_books": 1,
        "vedabase_verses": 1,
        "concepts": len(vanipedia_data),
        "merged_verses": len(merged_verses),
        "output_dir": str(output_dir)
    }

    summary_file = output_dir / "pipeline_complete.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Print results
    print("\n" + "="*60)
    print("✓ PHASE 0 DEMO COMPLETE")
    print("="*60)
    print(f"\nResults:")
    print(f"  • PDF Verses: {summary['pdf_verses']}")
    print(f"  • VedaBase Books: {summary['vedabase_books']}")
    print(f"  • VedaBase Verses: {summary['vedabase_verses']}")
    print(f"  • Concepts: {summary['concepts']}")
    print(f"  • Merged Verses: {summary['merged_verses']}")
    print(f"\nOutput files:")
    print(f"  • {merged_file}")
    print(f"  • {concepts_file}")
    print(f"  • {summary_file}")
    print("\n✓ Data ready for Phase A (Obsidian vault creation)")


if __name__ == "__main__":
    asyncio.run(run_demo())
