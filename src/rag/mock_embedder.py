"""
Mock Embedder for testing Phase B without network access
Generates deterministic embeddings from text hashes
"""

import hashlib
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockEmbedder:
    """Mock embedder that generates consistent embeddings without network"""

    def __init__(self, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
        self.embedding_cache = {}
        logger.info(f"✓ Mock embedder initialized (dim: {embedding_dim})")

    def _text_to_embedding(self, text: str) -> list:
        """Generate deterministic embedding from text hash"""
        # Create hash for reproducibility
        hash_obj = hashlib.sha256(text.encode())
        hash_int = int(hash_obj.hexdigest(), 16)

        # Use hash to seed numpy for deterministic random generation
        np.random.seed(hash_int % (2**32))

        # Generate embedding
        embedding = np.random.randn(self.embedding_dim).astype(np.float32)

        # Normalize
        embedding = embedding / np.linalg.norm(embedding)

        return embedding.tolist()

    def embed_text(self, text: str) -> list:
        """Embed single text"""
        text_hash = hashlib.sha256(text.encode()).hexdigest()

        if text_hash not in self.embedding_cache:
            self.embedding_cache[text_hash] = self._text_to_embedding(text)

        return self.embedding_cache[text_hash]

    def embed_batch(self, texts: list, batch_size: int = 32) -> list:
        """Embed batch of texts"""
        return [self.embed_text(text) for text in texts]

    def similarity(self, emb1: list, emb2: list) -> float:
        """Cosine similarity"""
        vec1 = np.array(emb1)
        vec2 = np.array(emb2)

        dot = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot / (norm1 * norm2))

    def similarity_batch(self, query_emb: list, embeddings: list) -> list:
        """Batch similarity"""
        return [self.similarity(query_emb, emb) for emb in embeddings]

    def get_embedding_dimension(self) -> int:
        """Get dimension"""
        return self.embedding_dim

    def clear_cache(self):
        """Clear cache"""
        self.embedding_cache.clear()
