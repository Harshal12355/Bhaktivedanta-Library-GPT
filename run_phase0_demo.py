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
            "definition": "Religious duty; righteousness; cosmic law; the natural order of the universe",
            "synonyms": ["duty", "righteousness", "law", "cosmic order"],
            "related_concepts": ["Karma", "Yoga", "Atman"]
        },
        "Bhakti": {
            "id": "bhakti",
            "title": "Bhakti",
            "definition": "Devotion; loving service to the Supreme Lord; the path of devotional surrender",
            "synonyms": ["devotion", "love", "service", "surrender"],
            "related_concepts": ["Krishna", "Love", "Surrender"]
        },
        "Yoga": {
            "id": "yoga",
            "title": "Yoga",
            "definition": "Union; skill in action; spiritual discipline; methods of connecting with the divine",
            "synonyms": ["union", "discipline", "skill", "practice"],
            "related_concepts": ["Meditation", "Action", "Atman", "Brahman"]
        },
        "Atman": {
            "id": "atman",
            "title": "Atman",
            "definition": "The eternal individual soul; the self; the divine essence within all beings",
            "synonyms": ["soul", "self", "spirit"],
            "related_concepts": ["Brahman", "Maya", "Consciousness"]
        },
        "Brahman": {
            "id": "brahman",
            "title": "Brahman",
            "definition": "The ultimate reality; the absolute consciousness; the source of all existence",
            "synonyms": ["ultimate reality", "absolute", "supreme consciousness"],
            "related_concepts": ["Atman", "Maya", "Moksha"]
        },
        "Karma": {
            "id": "karma",
            "title": "Karma",
            "definition": "Action and its consequences; the universal law of cause and effect",
            "synonyms": ["action", "deed", "consequence"],
            "related_concepts": ["Dharma", "Rebirth", "Causality"]
        },
        "Moksha": {
            "id": "moksha",
            "title": "Moksha",
            "definition": "Liberation; freedom from the cycle of rebirth; union with the divine",
            "synonyms": ["liberation", "salvation", "freedom"],
            "related_concepts": ["Brahman", "Atman", "Yoga"]
        }
    }
    print(f"✓ Generated mock Vanipedia: {len(vanipedia_data)} concepts")

    # Step 4: Merge all data with concept mapping
    print("\n[STEP 4/4] Merging data sources...")

    concept_mapping = {
        "BG-1.1": ["Dharma", "Yoga"],
        "BG-1.2": ["Dharma"],
        "BG-2.47": ["Yoga", "Karma"],
        "BG-3.35": ["Dharma", "Karma"],
        "BG-4.13": ["Dharma"],
        "BG-6.46": ["Yoga", "Bhakti"],
        "BG-13.2": ["Atman", "Brahman"],
        "BG-18.66": ["Bhakti", "Moksha"],
        "Isha-1": ["Brahman"],
        "Katha-2.3.1": ["Atman", "Yoga"],
        "Mundaka-2.2.11": ["Brahman", "Atman", "Moksha"],
        "Chandogya-3.14.1": ["Atman", "Brahman"],
        "BS-1.1.1": ["Brahman"],
        "BS-1.1.2": ["Brahman", "Karma"],
    }

    merged_verses = {}
    for key, verse in pdf_verses.items():
        concepts = concept_mapping.get(key, ["Dharma", "Yoga"])
        merged_verses[key] = {
            "reference": key,
            "chapter": verse["chapter"],
            "verse": verse["verse"],
            "source": verse["source"],
            "text": verse["text"],
            "translation": verse["translation"],
            "concepts": concepts
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
