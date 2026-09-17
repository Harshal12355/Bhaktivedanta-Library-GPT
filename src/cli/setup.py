"""
RAG Setup for CLI
Initialize RAG system with Phase 0 data
"""

import json
import sys
from pathlib import Path

from ..rag import VectorStore, Retriever, RAGEngine, LLMInterface
from .formatter import print_header, print_success, print_error


def setup_rag():
    """Initialize RAG system"""

    print_header("Initializing Vedic RAG System")

    # Load Phase 0 data
    print("📂 Loading Phase 0 data...")

    verses_file = Path("./data/pipeline_output/merged_verses.json")
    concepts_file = Path("./data/pipeline_output/concepts.json")

    verses = []
    concepts = []

    if not verses_file.exists():
        print_error("Phase 0 data not found. Run: python run_phase0_demo.py")
        return False

    with open(verses_file, "r", encoding="utf-8") as f:
        verse_data = json.load(f)
        for ref, data in verse_data.items():
            verse = {
                "id": data.get("reference", ref),
                "chapter": data.get("chapter"),
                "verse_number": data.get("verse"),
                "translation": data.get("sources", {}).get("translation"),
                "themes": data.get("concepts", []),
            }
            verses.append(verse)

    print_success(f"Loaded {len(verses)} verses")

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

        print_success(f"Loaded {len(concepts)} concepts")

    # Initialize vector store
    print("\n📦 Initializing vector store...")
    vector_store = VectorStore(
        db_url="sqlite:///vedic_rag.db",
        use_mock=True  # Use mock embedder
    )
    print_success("Vector store initialized")

    # Index data
    print("\n🔍 Indexing verses...")
    vector_store.index_verses(verses)

    print("🔍 Indexing concepts...")
    vector_store.index_concepts(concepts)

    # Initialize components
    print("\n🔧 Initializing RAG components...")
    retriever = Retriever(vector_store, vector_store.embedder)
    llm = LLMInterface(use_deepseek=False)
    rag_engine = RAGEngine(vector_store, retriever, llm)

    print_success("RAG system initialized!")

    # Display stats
    stats = rag_engine.stats()
    print("\n📊 System Statistics:")
    print(f"  Verses: {stats['vector_store']['total_verses']}")
    print(f"  Concepts: {stats['vector_store']['total_concepts']}")
    print(f"  Embeddings: {stats['vector_store']['embedding_model']}")
    print(f"  LLM: {stats['llm_model']}")

    return True
