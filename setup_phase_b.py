#!/usr/bin/env python3
"""
Phase B Setup: Initialize RAG System
Loads Phase 0 data into vector store and tests retrieval
"""

import json
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rag import VectorStore, Retriever, RAGEngine, LLMInterface

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_phase0_data():
    """Load data from Phase 0 pipeline"""

    verses_file = Path("./data/pipeline_output/merged_verses.json")
    concepts_file = Path("./data/pipeline_output/concepts.json")

    verses = []
    concepts = []

    if verses_file.exists():
        with open(verses_file, "r", encoding="utf-8") as f:
            verse_data = json.load(f)
            # Convert format
            for ref, data in verse_data.items():
                verse = {
                    "id": data.get("reference", ref),
                    "chapter": data.get("chapter"),
                    "verse_number": data.get("verse"),
                    "translation": data.get("sources", {}).get("translation"),
                    "themes": data.get("concepts", []),
                }
                verses.append(verse)
        logger.info(f"✓ Loaded {len(verses)} verses from Phase 0")

    if concepts_file.exists():
        with open(concepts_file, "r", encoding="utf-8") as f:
            concept_data = json.load(f)
            for name, data in concept_data.items():
                concept = {
                    "id": data.get("id", name.lower()),
                    "name": data.get("title", name),
                    "definition": data.get("definition", ""),
                    "description": data.get("description"),
                    "synonyms": data.get("synonyms", []),
                    "related_concepts": data.get("related_concepts", []),
                }
                concepts.append(concept)
        logger.info(f"✓ Loaded {len(concepts)} concepts from Phase 0")

    return verses, concepts


def setup_rag_system():
    """Setup and initialize RAG system"""

    logger.info("=" * 60)
    logger.info("PHASE B: RAG SYSTEM SETUP")
    logger.info("=" * 60)

    # Initialize vector store (use mock embedder for demo)
    logger.info("\n[STEP 1] Initializing vector store...")
    vector_store = VectorStore(
        db_url="sqlite:///vedic_rag.db",
        embedding_model="BAAI/bge-small-en-v1.5",
        use_mock=True  # Use mock embedder for testing without network
    )

    # Load Phase 0 data
    logger.info("\n[STEP 2] Loading Phase 0 data...")
    verses, concepts = load_phase0_data()

    if not verses:
        logger.error("No verses found. Run Phase 0 first.")
        return False

    # Index verses
    logger.info("\n[STEP 3] Indexing verses with embeddings...")
    vector_store.index_verses(verses)

    # Index concepts
    logger.info("\n[STEP 4] Indexing concepts with embeddings...")
    vector_store.index_concepts(concepts)

    # Display stats
    logger.info("\n[STEP 5] Vector store statistics:")
    stats = vector_store.stats()
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")

    # Initialize retriever
    logger.info("\n[STEP 6] Initializing retriever...")
    retriever = Retriever(vector_store, vector_store.embedder)

    # Initialize LLM
    logger.info("\n[STEP 7] Initializing LLM interface...")
    llm = LLMInterface(use_deepseek=False)  # Start with Ollama for testing
    logger.info(f"  LLM Model: {llm.model}")
    logger.info(f"  Using DeepSeek: {llm.use_deepseek}")

    # Initialize RAG engine
    logger.info("\n[STEP 8] Initializing RAG engine...")
    rag_engine = RAGEngine(vector_store, retriever, llm)

    # Test retrieval
    logger.info("\n[STEP 9] Testing retrieval...")
    test_query = "What is Dharma?"
    test_result = retriever.retrieve(test_query)
    logger.info(f"  Query: {test_query}")
    logger.info(f"  Verses found: {len(test_result['verses'])}")
    logger.info(f"  Concepts found: {len(test_result['concepts'])}")

    if test_result["verses"]:
        logger.info(f"  Top verse: {test_result['verses'][0]['id']}")

    logger.info("\n" + "=" * 60)
    logger.info("✓ PHASE B SETUP COMPLETE")
    logger.info("=" * 60)
    logger.info("\nRAG System ready for queries!")
    logger.info("Database: vedic_rag.db")
    logger.info("Embedding model: BAAI/bge-small-en-v1.5")
    logger.info("\nNext: Start Phase C (chat interface)")

    return True


if __name__ == "__main__":
    try:
        success = setup_rag_system()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Setup failed: {e}", exc_info=True)
        sys.exit(1)
