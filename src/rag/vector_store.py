"""
Vector Store
Manages vector embeddings and similarity search
Uses SQLite with JSON for embeddings (pgvector for production)
"""

import json
import logging
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from pathlib import Path

from .db_models import Verse, Concept, EmbeddingCache, DatabaseConfig
from .embedder import TextEmbedder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStore:
    """Vector store for semantic search over verses and concepts"""

    def __init__(
        self,
        db_url: str = "sqlite:///vedic_rag.db",
        embedding_model: str = "BAAI/bge-small-en-v1.5",
        use_mock: bool = False,
    ):
        self.db_config = DatabaseConfig(db_url)
        self.db_config.init_db()

        # Try real embedder, fall back to mock
        if use_mock:
            from .mock_embedder import MockEmbedder
            logger.info("Using mock embedder for testing")
            self.embedder = MockEmbedder()
        else:
            try:
                self.embedder = TextEmbedder(model_name=embedding_model)
            except Exception as e:
                logger.warning(f"TextEmbedder failed, using mock: {e}")
                from .mock_embedder import MockEmbedder
                self.embedder = MockEmbedder()

        self.embedding_model = embedding_model

    def index_verses(self, verses: List[Dict], batch_size: int = 32):
        """Index verses with embeddings"""
        logger.info(f"Indexing {len(verses)} verses...")
        session = self.db_config.get_session()

        try:
            # Prepare texts for embedding
            texts_to_embed = []
            verse_objs = []

            for verse_data in verses:
                verse_id = verse_data.get("id") or f"BG-{verse_data['chapter']}.{verse_data['verse_number']}"

                # Check if verse already exists
                existing = session.query(Verse).filter(Verse.id == verse_id).first()
                if existing and existing.embedding:
                    continue  # Skip already indexed

                # Create verse object
                verse_obj = Verse(
                    id=verse_id,
                    chapter=verse_data.get("chapter"),
                    verse_number=verse_data.get("verse_number"),
                    devanagari=verse_data.get("devanagari"),
                    transliteration=verse_data.get("transliteration"),
                    translation=verse_data.get("translation"),
                    purport=verse_data.get("purport"),
                    themes=verse_data.get("themes", []),
                    source_text=verse_data.get("source_text", "Bhagavad-Gita"),
                )

                # Prepare text for embedding
                text_to_embed = f"{verse_obj.transliteration or ''} {verse_obj.translation or ''}"
                if text_to_embed.strip():
                    texts_to_embed.append(text_to_embed)
                    verse_objs.append(verse_obj)

            # Generate embeddings in batch
            if texts_to_embed:
                embeddings = self.embedder.embed_batch(texts_to_embed, batch_size=batch_size)

                # Save to database
                for verse_obj, embedding in zip(verse_objs, embeddings):
                    verse_obj.embedding = json.dumps(embedding)
                    verse_obj.embedding_model = self.embedding_model
                    session.merge(verse_obj)

            session.commit()
            logger.info(f"✓ Indexed {len(verse_objs)} verses")

        except Exception as e:
            session.rollback()
            logger.error(f"Error indexing verses: {e}")
            raise

        finally:
            session.close()

    def index_concepts(self, concepts: List[Dict]):
        """Index concepts with embeddings"""
        logger.info(f"Indexing {len(concepts)} concepts...")
        session = self.db_config.get_session()

        try:
            for concept_data in concepts:
                concept_id = concept_data.get("id", concept_data.get("name", "").lower())

                # Check if exists
                existing = session.query(Concept).filter(Concept.id == concept_id).first()
                if existing and existing.embedding:
                    continue

                # Create concept object
                concept = Concept(
                    id=concept_id,
                    name=concept_data.get("name"),
                    definition=concept_data.get("definition", ""),
                    description=concept_data.get("description"),
                    synonyms=concept_data.get("synonyms", []),
                    related_concepts=concept_data.get("related_concepts", []),
                )

                # Generate embedding
                text_to_embed = f"{concept.name} {concept.definition}"
                embedding = self.embedder.embed_text(text_to_embed)

                concept.embedding = json.dumps(embedding)
                concept.embedding_model = self.embedding_model

                session.merge(concept)

            session.commit()
            logger.info(f"✓ Indexed {len(concepts)} concepts")

        except Exception as e:
            session.rollback()
            logger.error(f"Error indexing concepts: {e}")
            raise

        finally:
            session.close()

    def search_verses(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search verses by semantic similarity"""
        session = self.db_config.get_session()

        try:
            # Embed query
            query_embedding = self.embedder.embed_text(query)
            query_embedding_str = json.dumps(query_embedding)

            # Get all verses with embeddings
            verses = session.query(Verse).filter(Verse.embedding.isnot(None)).all()

            if not verses:
                logger.warning("No indexed verses found")
                return []

            # Compute similarities
            similarities = []
            for verse in verses:
                verse_embedding = json.loads(verse.embedding)
                sim = self.embedder.similarity(query_embedding, verse_embedding)
                similarities.append((verse, sim))

            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)

            # Return top-k
            results = []
            for verse, score in similarities[:top_k]:
                results.append({
                    "id": verse.id,
                    "reference": verse.id,
                    "chapter": verse.chapter,
                    "verse": verse.verse_number,
                    "translation": verse.translation,
                    "themes": verse.themes,
                    "score": float(score),
                })

            return results

        finally:
            session.close()

    def search_concepts(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search concepts by semantic similarity"""
        session = self.db_config.get_session()

        try:
            # Embed query
            query_embedding = self.embedder.embed_text(query)

            # Get all concepts with embeddings
            concepts = session.query(Concept).filter(Concept.embedding.isnot(None)).all()

            if not concepts:
                logger.warning("No indexed concepts found")
                return []

            # Compute similarities
            similarities = []
            for concept in concepts:
                concept_embedding = json.loads(concept.embedding)
                sim = self.embedder.similarity(query_embedding, concept_embedding)
                similarities.append((concept, sim))

            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)

            # Return top-k
            results = []
            for concept, score in similarities[:top_k]:
                results.append({
                    "id": concept.id,
                    "name": concept.name,
                    "definition": concept.definition,
                    "score": float(score),
                })

            return results

        finally:
            session.close()

    def get_verse_by_id(self, verse_id: str) -> Optional[Dict]:
        """Get verse by ID"""
        session = self.db_config.get_session()

        try:
            verse = session.query(Verse).filter(Verse.id == verse_id).first()
            if verse:
                return verse.to_dict()
            return None

        finally:
            session.close()

    def get_concept_by_id(self, concept_id: str) -> Optional[Dict]:
        """Get concept by ID"""
        session = self.db_config.get_session()

        try:
            concept = session.query(Concept).filter(Concept.id == concept_id).first()
            if concept:
                return concept.to_dict()
            return None

        finally:
            session.close()

    def stats(self) -> Dict:
        """Get vector store statistics"""
        session = self.db_config.get_session()

        try:
            verse_count = session.query(Verse).count()
            concept_count = session.query(Concept).count()
            indexed_verses = session.query(Verse).filter(Verse.embedding.isnot(None)).count()
            indexed_concepts = session.query(Concept).filter(Concept.embedding.isnot(None)).count()

            return {
                "total_verses": verse_count,
                "indexed_verses": indexed_verses,
                "total_concepts": concept_count,
                "indexed_concepts": indexed_concepts,
                "embedding_model": self.embedding_model,
                "embedding_dimension": self.embedder.get_embedding_dimension(),
            }

        finally:
            session.close()
