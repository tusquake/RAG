import os
import pickle
from typing import List, Dict, Optional, Tuple
import numpy as np

from app.config import get_settings

settings = get_settings()


class VectorStore:
    def __init__(self):
        self.indexes = {}
        self.documents = {}
    
    async def create_index(
        self,
        document_id: str,
        chunks: List[Dict],
        embeddings: List[List[float]]
    ):
        import faiss
        
        vectors = np.array(embeddings).astype('float32')
        
        dimension = vectors.shape[1]
        index = faiss.IndexFlatIP(dimension)
        index.add(vectors)
        
        self.indexes[document_id] = index
        self.documents[document_id] = chunks
        
        await self._save_index(document_id)
    
    async def search(
        self,
        document_id: str,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict]:
        if document_id not in self.indexes:
            await self._load_index(document_id)
        
        if document_id not in self.indexes:
            return []
        
        index = self.indexes[document_id]
        chunks = self.documents[document_id]
        
        query = np.array([query_embedding]).astype('float32')
        scores, indices = index.search(query, min(top_k, len(chunks)))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(chunks):
                chunk = chunks[idx].copy()
                chunk["score"] = float(score)
                results.append(chunk)
        
        return results
    
    async def delete_index(self, document_id: str):
        if document_id in self.indexes:
            del self.indexes[document_id]
        if document_id in self.documents:
            del self.documents[document_id]
        
        index_path = self._get_index_path(document_id)
        docs_path = self._get_docs_path(document_id)
        
        if os.path.exists(index_path):
            os.remove(index_path)
        if os.path.exists(docs_path):
            os.remove(docs_path)
    
    def _get_index_path(self, document_id: str) -> str:
        return os.path.join(settings.FAISS_INDEX_PATH, f"{document_id}.index")
    
    def _get_docs_path(self, document_id: str) -> str:
        return os.path.join(settings.FAISS_INDEX_PATH, f"{document_id}.pkl")
    
    async def _save_index(self, document_id: str):
        import faiss
        import asyncio
        
        os.makedirs(settings.FAISS_INDEX_PATH, exist_ok=True)
        
        index = self.indexes[document_id]
        chunks = self.documents[document_id]
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            faiss.write_index,
            index,
            self._get_index_path(document_id)
        )
        
        with open(self._get_docs_path(document_id), 'wb') as f:
            pickle.dump(chunks, f)
    
    async def _load_index(self, document_id: str):
        import faiss
        import asyncio
        
        index_path = self._get_index_path(document_id)
        docs_path = self._get_docs_path(document_id)
        
        if not os.path.exists(index_path) or not os.path.exists(docs_path):
            return
        
        loop = asyncio.get_event_loop()
        index = await loop.run_in_executor(
            None,
            faiss.read_index,
            index_path
        )
        
        with open(docs_path, 'rb') as f:
            chunks = pickle.load(f)
        
        self.indexes[document_id] = index
        self.documents[document_id] = chunks


vector_store = VectorStore()
