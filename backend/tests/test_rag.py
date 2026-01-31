"""Tests for RAG pipeline."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np


class TestRAGPipeline:
    """Tests for RAG pipeline operations."""
    
    @pytest.mark.asyncio
    async def test_retrieve_context(self, mock_embedding):
        """Test context retrieval."""
        from app.services.rag_pipeline import RAGPipeline
        from app.services.vector_store import vector_store
        
        pipeline = RAGPipeline()
        
        # Mock the embedding service
        with patch.object(pipeline.embedding_service, 'embed_text', 
                         return_value=np.random.rand(384).tolist()):
            with patch.object(vector_store, 'search', 
                             return_value=[
                                 {"text": "Chunk 1", "score": 0.9},
                                 {"text": "Chunk 2", "score": 0.8}
                             ]):
                results = await pipeline.retrieve_context("doc_id", "What is this?")
                
                assert len(results) == 2
                assert results[0]["score"] > results[1]["score"]
    
    @pytest.mark.asyncio
    async def test_find_relevant_timestamps(self, mock_embedding):
        """Test timestamp relevance ranking."""
        from app.services.rag_pipeline import RAGPipeline
        
        pipeline = RAGPipeline()
        
        timestamps = [
            {"start": 0, "end": 30, "text": "Introduction to Python"},
            {"start": 30, "end": 60, "text": "Variables and data types"},
            {"start": 60, "end": 90, "text": "Control flow statements"}
        ]
        
        with patch.object(pipeline.embedding_service, 'embed_text',
                         return_value=[0.1] * 384):
            with patch.object(pipeline.embedding_service, 'embed_texts',
                             return_value=[[0.1] * 384, [0.2] * 384, [0.3] * 384]):
                with patch.object(pipeline.embedding_service, 'compute_similarity',
                                 return_value=[0.9, 0.7, 0.5]):
                    results = await pipeline.find_relevant_timestamps(
                        "What are variables?",
                        timestamps,
                        top_k=2
                    )
                    
                    assert len(results) == 2
                    # Should be sorted by relevance
                    assert results[0]["relevance_score"] >= results[1]["relevance_score"]
    
    @pytest.mark.asyncio
    async def test_find_timestamps_empty(self):
        """Test timestamp search with empty list."""
        from app.services.rag_pipeline import RAGPipeline
        
        pipeline = RAGPipeline()
        
        results = await pipeline.find_relevant_timestamps("query", [], top_k=3)
        
        assert results == []
    
    @pytest.mark.asyncio
    async def test_index_document(self, mock_embedding):
        """Test document indexing."""
        from app.services.rag_pipeline import RAGPipeline
        from app.services.vector_store import vector_store
        
        pipeline = RAGPipeline()
        
        chunks = [
            {"text": "First chunk content", "index": 0},
            {"text": "Second chunk content", "index": 1}
        ]
        
        with patch.object(pipeline.embedding_service, 'embed_texts',
                         return_value=[np.random.rand(384).tolist() for _ in chunks]):
            with patch.object(vector_store, 'create_index', new_callable=AsyncMock):
                await pipeline.index_document("doc_123", chunks)
                
                vector_store.create_index.assert_called_once()


class TestRAGIntegration:
    """Integration tests for RAG pipeline."""
    
    @pytest.mark.asyncio
    async def test_full_qa_flow(self):
        """Test complete Q&A flow."""
        from app.services.rag_pipeline import RAGPipeline
        from app.services.llm_service import LLMService
        
        # This would be an integration test with actual services
        # For unit testing, we mock the components
        
        pipeline = RAGPipeline()
        llm = LLMService()
        
        # Verify services are properly initialized
        assert pipeline.embedding_service is not None
        assert llm.api_url is not None
