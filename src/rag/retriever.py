"""
Retriever
Hybrid retrieval combining semantic search and concept filtering
"""

import logging
from typing import List, Dict, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Retriever:
    """Hybrid retriever for verses and concepts"""

    def __init__(self, vector_store, embedder):
        self.vector_store = vector_store
        self.embedder = embedder

    def retrieve(
        self,
        query: str,
        top_k_verses: int = 5,
        top_k_concepts: int = 3,
        use_concept_filter: bool = True,
    ) -> Dict:
        """Retrieve verses and concepts for a query"""

        logger.info(f"Retrieving context for: {query}")

        # Step 1: Semantic search
        verses = self.vector_store.search_verses(query, top_k=top_k_verses * 2)
        concepts = self.vector_store.search_concepts(query, top_k=top_k_concepts * 2)

        # Step 2: Concept filtering (optional)
        if use_concept_filter and concepts:
            concepts = self._filter_by_concept_match(verses, concepts, top_k_concepts)
        else:
            concepts = concepts[:top_k_concepts]

        # Step 3: Rank verses by concept relevance
        verses = self._rank_by_concepts(verses, concepts, top_k_verses)

        result = {
            "query": query,
            "verses": verses,
            "concepts": concepts,
            "retrieved_count": len(verses) + len(concepts),
        }

        logger.info(f"Retrieved {len(verses)} verses and {len(concepts)} concepts")
        return result

    def _filter_by_concept_match(
        self,
        verses: List[Dict],
        concepts: List[Dict],
        top_k: int,
    ) -> List[Dict]:
        """Boost concepts that match verse themes"""
        concept_scores = {}

        # Calculate boost based on verse theme matches
        for concept in concepts:
            concept_name = concept.get("name", "")
            matches = sum(
                1 for verse in verses
                if concept_name in verse.get("themes", [])
            )

            # Boost score by match count
            concept_scores[concept_name] = concept.get("score", 0) + (matches * 0.1)

        # Re-rank by boosted score
        boosted = []
        for concept in concepts:
            concept_copy = concept.copy()
            concept_copy["score"] = concept_scores.get(concept["name"], concept["score"])
            boosted.append(concept_copy)

        boosted.sort(key=lambda x: x["score"], reverse=True)
        return boosted[:top_k]

    def _rank_by_concepts(
        self,
        verses: List[Dict],
        concepts: List[Dict],
        top_k: int,
    ) -> List[Dict]:
        """Boost verses that mention retrieved concepts"""
        concept_names = {c.get("name") for c in concepts}

        # Calculate boosted scores
        boosted = []
        for verse in verses:
            verse_copy = verse.copy()

            # Count matching concepts in verse themes
            theme_matches = sum(
                1 for theme in verse.get("themes", [])
                if theme in concept_names
            )

            # Boost score by theme matches
            verse_copy["score"] = verse.get("score", 0) + (theme_matches * 0.15)
            boosted.append(verse_copy)

        # Sort by boosted score
        boosted.sort(key=lambda x: x["score"], reverse=True)
        return boosted[:top_k]

    def retrieve_by_concept(self, concept_name: str) -> List[Dict]:
        """Get all verses related to a concept"""
        concept = self.vector_store.get_concept_by_id(concept_name.lower())

        if not concept:
            logger.warning(f"Concept not found: {concept_name}")
            return []

        # Semantic search using concept definition
        verses = self.vector_store.search_verses(
            concept.get("definition", concept_name),
            top_k=20,
        )

        logger.info(f"Found {len(verses)} verses for concept: {concept_name}")
        return verses

    def retrieve_by_chapter(self, chapter: int) -> List[Dict]:
        """Get all verses in a chapter"""
        session = self.vector_store.db_config.get_session()

        try:
            from .db_models import Verse
            verses = session.query(Verse).filter(Verse.chapter == chapter).all()

            results = [v.to_dict() for v in verses]
            logger.info(f"Found {len(results)} verses in chapter {chapter}")
            return results

        finally:
            session.close()

    def retrieve_similar_verses(self, verse_id: str, top_k: int = 5) -> List[Dict]:
        """Find verses similar to a given verse"""
        verse = self.vector_store.get_verse_by_id(verse_id)

        if not verse:
            logger.warning(f"Verse not found: {verse_id}")
            return []

        # Use translation and concepts to find similar verses
        query = f"{verse.get('translation', '')} {' '.join(verse.get('themes', []))}"
        similar = self.vector_store.search_verses(query, top_k=top_k + 1)

        # Remove the original verse from results
        similar = [v for v in similar if v["id"] != verse_id][:top_k]

        logger.info(f"Found {len(similar)} verses similar to {verse_id}")
        return similar


if __name__ == "__main__":
    # Test retriever
    from vector_store import VectorStore

    print("\n=== Testing Retriever ===\n")

    vector_store = VectorStore()
    retriever = Retriever(vector_store, vector_store.embedder)

    # Example retrieval
    result = retriever.retrieve("What is the purpose of Yoga?")
    print(f"Query: {result['query']}")
    print(f"Verses found: {len(result['verses'])}")
    print(f"Concepts found: {len(result['concepts'])}")
