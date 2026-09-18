"""
Embedder Service
Handles text embeddings using sentence-transformers (BAAI/bge-small)
"""

import hashlib
import json
import logging
from typing import List, Dict, Optional
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    logger.warning("sentence-transformers not installed. Install: pip install sentence-transformers")


class TextEmbedder:
    """Generate and manage text embeddings"""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", use_cache: bool = True):
        if not HAS_SENTENCE_TRANSFORMERS:
            raise ImportError("sentence-transformers required. Install: pip install sentence-transformers")

        self.model_name = model_name
        self.use_cache = use_cache
        self.embedding_cache: Dict[str, List[float]] = {}

        logger.info(f"Loading embedding model: {model_name}")
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"✓ Model loaded. Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def _get_text_hash(self, text: str) -> str:
        """Get SHA256 hash of text for caching"""
        return hashlib.sha256(text.encode()).hexdigest()

    def embed_text(self, text: str) -> List[float]:
        """Embed a single text string"""
        text_hash = self._get_text_hash(text)

        # Check cache
        if self.use_cache and text_hash in self.embedding_cache:
            return self.embedding_cache[text_hash]

        try:
            embedding = self.model.encode(text, convert_to_numpy=False)
            embedding_list = embedding.tolist() if hasattr(embedding, 'tolist') else embedding

            # Cache result
            if self.use_cache:
                self.embedding_cache[text_hash] = embedding_list

            return embedding_list
        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            raise

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Embed multiple texts efficiently"""
        embeddings = []

        for text in texts:
            text_hash = self._get_text_hash(text)

            # Check cache
            if self.use_cache and text_hash in self.embedding_cache:
                embeddings.append(self.embedding_cache[text_hash])
            else:
                embeddings.append(None)  # Placeholder

        # Find texts to embed (not cached)
        texts_to_embed = [text for text, emb in zip(texts, embeddings) if emb is None]

        if texts_to_embed:
            try:
                batch_embeddings = self.model.encode(texts_to_embed, batch_size=batch_size, convert_to_numpy=False)
                batch_embeddings = [e.tolist() if hasattr(e, 'tolist') else e for e in batch_embeddings]

                # Fill in placeholders and cache
                idx = 0
                for i, emb in enumerate(embeddings):
                    if emb is None:
                        embeddings[i] = batch_embeddings[idx]
                        if self.use_cache:
                            text_hash = self._get_text_hash(texts[i])
                            self.embedding_cache[text_hash] = batch_embeddings[idx]
                        idx += 1
            except Exception as e:
                logger.error(f"Error in batch embedding: {e}")
                raise

        return embeddings

    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between two embeddings"""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def similarity_batch(self, query_embedding: List[float], embeddings: List[List[float]]) -> List[float]:
        """Compute similarity between query and multiple embeddings"""
        query_vec = np.array(query_embedding)
        similarities = []

        for emb in embeddings:
            emb_vec = np.array(emb)
            dot_product = np.dot(query_vec, emb_vec)
            norm_q = np.linalg.norm(query_vec)
            norm_e = np.linalg.norm(emb_vec)

            if norm_q == 0 or norm_e == 0:
                similarities.append(0.0)
            else:
                similarities.append(float(dot_product / (norm_q * norm_e)))

        return similarities

    def get_embedding_dimension(self) -> int:
        """Get embedding vector dimension"""
        return self.model.get_sentence_embedding_dimension()

    def clear_cache(self):
        """Clear embedding cache"""
        self.embedding_cache.clear()
        logger.info("Embedding cache cleared")


if __name__ == "__main__":
    # Test embedder
    embedder = TextEmbedder()

    test_texts = [
        "What is Dharma?",
        "Dharma means religious duty",
        "The Bhagavad Gita teaches Yoga",
    ]

    print("\n=== Testing Embedder ===\n")

    # Single text
    emb1 = embedder.embed_text(test_texts[0])
    print(f"Embedding dimension: {len(emb1)}")
    print(f"Sample embedding (first 5 values): {emb1[:5]}")

    # Batch
    print("\n=== Batch Embeddings ===")
    batch_embeddings = embedder.embed_batch(test_texts)
    print(f"Generated {len(batch_embeddings)} embeddings")

    # Similarity
    print("\n=== Similarity Scores ===")
    sim = embedder.similarity(batch_embeddings[0], batch_embeddings[1])
    print(f"'What is Dharma?' vs 'Dharma means religious duty': {sim:.4f}")

    sims = embedder.similarity_batch(batch_embeddings[0], batch_embeddings[1:])
    print(f"Query similarities: {[f'{s:.4f}' for s in sims]}")
