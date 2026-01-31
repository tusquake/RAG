from typing import List
import numpy as np

from app.config import get_settings

settings = get_settings()


class EmbeddingService:
    _model = None
    
    @classmethod
    def get_model(cls):
        if cls._model is None:
            from sentence_transformers import SentenceTransformer
            cls._model = SentenceTransformer(settings.EMBEDDING_MODEL)
        return cls._model
    
    async def embed_text(self, text: str) -> List[float]:
        import asyncio
        
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            self._embed_sync,
            text
        )
        return embedding.tolist()
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        import asyncio
        
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            self._embed_batch_sync,
            texts
        )
        return [e.tolist() for e in embeddings]
    
    def _embed_sync(self, text: str) -> np.ndarray:
        model = self.get_model()
        return model.encode(text, normalize_embeddings=True)
    
    def _embed_batch_sync(self, texts: List[str]) -> np.ndarray:
        model = self.get_model()
        return model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    
    async def compute_similarity(
        self,
        query_embedding: List[float],
        document_embeddings: List[List[float]]
    ) -> List[float]:
        query = np.array(query_embedding)
        docs = np.array(document_embeddings)
        
        similarities = np.dot(docs, query)
        
        return similarities.tolist()
