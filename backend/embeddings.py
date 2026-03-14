import logging
from sentence_transformers import SentenceTransformer
from typing import List

logger = logging.getLogger(__name__)

# using MiniLM — lightweight, fast, 384-dim vectors, good enough for RAG
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class EmbeddingModel:
    """Wrapper around SentenceTransformers for generating text embeddings."""

    def __init__(self, model_name: str = MODEL_NAME):
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)

    def generate(self, text: str) -> List[float]:
        """Generate embedding for a single text string."""
        if not text or not text.strip():
            return []
        return self.model.encode(text).tolist()

    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts at once (faster than one-by-one)."""
        valid = [t for t in texts if t and t.strip()]
        if not valid:
            return []
        logger.info(f"Embedding {len(valid)} chunks")
        return self.model.encode(valid).tolist()


# single instance — model is expensive to load, so we reuse it
embedding_model = EmbeddingModel()
