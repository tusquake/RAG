from typing import List, Dict
from app.services.embedding import EmbeddingService
from app.services.vector_store import vector_store


class RAGPipeline:
    def __init__(self):
        self.embedding_service = EmbeddingService()
    
    async def retrieve_context(
        self,
        document_id: str,
        query: str,
        top_k: int = 5
    ) -> List[Dict]:
        query_embedding = await self.embedding_service.embed_text(query)
        
        results = await vector_store.search(
            document_id=document_id,
            query_embedding=query_embedding,
            top_k=top_k
        )
        
        return results
    
    async def find_relevant_timestamps(
        self,
        query: str,
        timestamps: List[Dict],
        top_k: int = 3
    ) -> List[Dict]:
        if not timestamps:
            return []
        
        query_embedding = await self.embedding_service.embed_text(query)
        
        timestamp_texts = [ts.get("text", "") for ts in timestamps]
        timestamp_embeddings = await self.embedding_service.embed_texts(timestamp_texts)
        
        similarities = await self.embedding_service.compute_similarity(
            query_embedding,
            timestamp_embeddings
        )
        
        scored_timestamps = [
            {
                "start": ts.get("start", 0),
                "end": ts.get("end", 0),
                "text": ts.get("text", ""),
                "relevance_score": float(score)
            }
            for ts, score in zip(timestamps, similarities)
        ]
        
        scored_timestamps.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return scored_timestamps[:top_k]
    
    async def index_document(
        self,
        document_id: str,
        chunks: List[Dict]
    ):
        texts = [chunk["text"] for chunk in chunks]
        embeddings = await self.embedding_service.embed_texts(texts)
        
        await vector_store.create_index(
            document_id=document_id,
            chunks=chunks,
            embeddings=embeddings
        )
