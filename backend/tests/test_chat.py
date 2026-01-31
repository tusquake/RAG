"""Tests for chat and RAG functionality."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np


class TestChatModels:
    """Tests for chat data models."""
    
    def test_chat_message_creation(self):
        """Test chat message model."""
        from app.models.chat import ChatMessage
        from datetime import datetime
        
        msg = ChatMessage(
            role="user",
            content="What is this document about?",
            timestamp=datetime.utcnow()
        )
        
        assert msg.role == "user"
        assert msg.content == "What is this document about?"
        assert msg.sources == []
    
    def test_chat_request_creation(self):
        """Test chat request model."""
        from app.models.chat import ChatRequest
        
        request = ChatRequest(
            message="Summarize the document",
            document_id="507f1f77bcf86cd799439012",
            stream=False
        )
        
        assert request.message == "Summarize the document"
        assert request.stream is False
    
    def test_chat_response_with_timestamps(self):
        """Test chat response with timestamps."""
        from app.models.chat import ChatResponse
        
        response = ChatResponse(
            message="Based on the document...",
            sources=[{"text": "Source text", "score": 0.9}],
            timestamps=[{"start": 10.5, "end": 20.0}]
        )
        
        assert len(response.sources) == 1
        assert len(response.timestamps) == 1


class TestEmbeddingService:
    """Tests for embedding service."""
    
    @pytest.mark.asyncio
    async def test_embed_text(self, mock_embedding):
        """Test single text embedding."""
        from app.services.embedding import EmbeddingService
        
        service = EmbeddingService()
        
        with patch.object(service, '_embed_sync', return_value=np.random.rand(384)):
            embedding = await service.embed_text("Test text")
            
            assert isinstance(embedding, list)
            assert len(embedding) == 384
    
    @pytest.mark.asyncio
    async def test_compute_similarity(self):
        """Test similarity computation."""
        from app.services.embedding import EmbeddingService
        
        service = EmbeddingService()
        
        # Create normalized vectors
        query = [1.0] * 384
        docs = [[1.0] * 384, [0.5] * 384]
        
        similarities = await service.compute_similarity(query, docs)
        
        assert len(similarities) == 2
        assert similarities[0] > similarities[1]


class TestPDFProcessor:
    """Tests for PDF processing."""
    
    def test_chunk_text_short(self):
        """Test chunking short text."""
        from app.services.pdf_processor import PDFProcessor
        
        processor = PDFProcessor()
        text = "This is a short text."
        
        chunks = processor.chunk_text(text, chunk_size=1000)
        
        assert len(chunks) == 1
        assert chunks[0]["text"] == text
    
    def test_chunk_text_with_overlap(self):
        """Test chunking with overlap."""
        from app.services.pdf_processor import PDFProcessor
        
        processor = PDFProcessor()
        
        # Create text longer than chunk size
        text = "Word " * 500  # ~2500 characters
        
        chunks = processor.chunk_text(text, chunk_size=500, overlap=100)
        
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk["text"]) <= 600  # chunk_size + some buffer


class TestTranscriptionService:
    """Tests for transcription service."""
    
    def test_extract_topics(self):
        """Test topic extraction from segments."""
        from app.services.transcription import TranscriptionService
        
        service = TranscriptionService()
        
        segments = [
            {"start": 0, "end": 10, "text": "Segment 1"},
            {"start": 10, "end": 20, "text": "Segment 2"},
            {"start": 20, "end": 30, "text": "Segment 3"},
            {"start": 30, "end": 40, "text": "Segment 4"},
            {"start": 40, "end": 50, "text": "Segment 5"},
            {"start": 50, "end": 60, "text": "Segment 6"},
        ]
        
        topics = service.extract_topics(segments)
        
        assert len(topics) >= 1
        assert topics[0]["start"] == 0


class TestVectorStore:
    """Tests for FAISS vector store."""
    
    @pytest.mark.asyncio
    async def test_create_and_search(self):
        """Test creating index and searching."""
        from app.services.vector_store import VectorStore
        import numpy as np
        
        store = VectorStore()
        
        # Create test data
        document_id = "test_doc_123"
        chunks = [
            {"text": "First chunk", "index": 0},
            {"text": "Second chunk", "index": 1}
        ]
        
        # Create random embeddings (384 dimensions for MiniLM)
        embeddings = [np.random.rand(384).tolist() for _ in chunks]
        
        # Create index
        await store.create_index(document_id, chunks, embeddings)
        
        assert document_id in store.indexes
        assert document_id in store.documents
        
        # Search
        query_embedding = np.random.rand(384).tolist()
        results = await store.search(document_id, query_embedding, top_k=2)
        
        assert len(results) == 2
        assert "score" in results[0]
    
    @pytest.mark.asyncio
    async def test_delete_index(self):
        """Test deleting an index."""
        from app.services.vector_store import VectorStore
        import numpy as np
        
        store = VectorStore()
        
        document_id = "test_doc_456"
        chunks = [{"text": "Test", "index": 0}]
        embeddings = [np.random.rand(384).tolist()]
        
        await store.create_index(document_id, chunks, embeddings)
        assert document_id in store.indexes
        
        await store.delete_index(document_id)
        assert document_id not in store.indexes


class TestLLMService:
    """Tests for LLM service."""
    
    def test_build_prompt(self):
        """Test prompt building."""
        from app.services.llm_service import LLMService
        
        service = LLMService()
        
        context_chunks = [
            {"text": "First context chunk"},
            {"text": "Second context chunk"}
        ]
        
        prompt = service._build_prompt(
            question="What is the main topic?",
            context_chunks=context_chunks,
            document_type="pdf"
        )
        
        assert "What is the main topic?" in prompt
        assert "First context chunk" in prompt
        assert "Second context chunk" in prompt
    
    def test_build_prompt_with_timestamps(self):
        """Test prompt building for audio/video."""
        from app.services.llm_service import LLMService
        
        service = LLMService()
        
        prompt = service._build_prompt(
            question="What is discussed at timestamp?",
            context_chunks=[{"text": "Audio content"}],
            document_type="audio"
        )
        
        assert "timestamps" in prompt.lower()
    
    def test_simple_summary(self):
        """Test simple summary generation."""
        from app.services.llm_service import LLMService
        
        service = LLMService()
        
        text = "This is sentence one. This is sentence two. This is sentence three."
        summary = service._simple_summary(text, max_words=10)
        
        assert len(summary.split()) <= 15  # Some buffer for sentence completion
    
    def test_fallback_response(self):
        """Test fallback response generation."""
        from app.services.llm_service import LLMService
        
        service = LLMService()
        
        # With context
        response = service._generate_fallback_response(
            "What is this?",
            [{"text": "Document content here"}]
        )
        assert "Document content" in response
        
        # Without context
        response = service._generate_fallback_response("What is this?", [])
        assert "couldn't find" in response.lower()
