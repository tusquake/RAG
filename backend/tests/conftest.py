"""Pytest configuration and fixtures."""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient
import os

# Set test environment variables
os.environ["MONGODB_URI"] = "mongodb://localhost:27017"
os.environ["MONGODB_DB_NAME"] = "document_qa_test"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["JWT_SECRET"] = "test-secret-key"
os.environ["HUGGINGFACE_API_KEY"] = "test-api-key"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_mongodb():
    """Mock MongoDB connection."""
    with patch("app.db.mongodb.mongodb") as mock:
        mock.db = MagicMock()
        mock.db.users = AsyncMock()
        mock.db.documents = AsyncMock()
        mock.db.chat_history = AsyncMock()
        yield mock


@pytest.fixture
def mock_redis():
    """Mock Redis connection."""
    with patch("app.db.redis.redis_client") as mock:
        mock.client = AsyncMock()
        mock.client.get = AsyncMock(return_value=None)
        mock.client.setex = AsyncMock()
        mock.client.incr = AsyncMock(return_value=1)
        mock.client.expire = AsyncMock()
        yield mock


@pytest.fixture
def test_user():
    """Sample test user data."""
    return {
        "id": "507f1f77bcf86cd799439011",
        "email": "test@example.com",
        "name": "Test User",
        "password": "testpassword123"
    }


@pytest.fixture
def auth_token(test_user):
    """Generate a valid auth token for testing."""
    from app.api.middleware.auth import create_access_token
    return create_access_token(
        data={"sub": test_user["id"], "email": test_user["email"]}
    )


@pytest.fixture
def auth_headers(auth_token):
    """Auth headers for authenticated requests."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def sample_document():
    """Sample document data."""
    return {
        "_id": "507f1f77bcf86cd799439012",
        "filename": "test.pdf",
        "original_filename": "test.pdf",
        "document_type": "pdf",
        "file_path": "/tmp/test.pdf",
        "file_size": 1024,
        "user_id": "507f1f77bcf86cd799439011",
        "status": "completed",
        "text_content": "This is a test document content.",
        "summary": None,
        "timestamps": []
    }


@pytest.fixture
def sample_audio_document():
    """Sample audio document data."""
    return {
        "_id": "507f1f77bcf86cd799439013",
        "filename": "test.mp3",
        "original_filename": "test.mp3",
        "document_type": "audio",
        "file_path": "/tmp/test.mp3",
        "file_size": 5120,
        "user_id": "507f1f77bcf86cd799439011",
        "status": "completed",
        "text_content": "This is transcribed audio content.",
        "duration": 120.5,
        "timestamps": [
            {"start": 0, "end": 30, "text": "Introduction section"},
            {"start": 30, "end": 60, "text": "Main content section"},
            {"start": 60, "end": 120, "text": "Conclusion section"}
        ]
    }


@pytest.fixture
def mock_whisper():
    """Mock Whisper transcription."""
    with patch("app.services.transcription.TranscriptionService._load_model") as mock:
        model = MagicMock()
        model.transcribe.return_value = {
            "text": "Transcribed text content",
            "segments": [
                {"start": 0, "end": 10, "text": "Segment 1"},
                {"start": 10, "end": 20, "text": "Segment 2"}
            ],
            "language": "en"
        }
        mock.return_value = model
        yield mock


@pytest.fixture
def mock_embedding():
    """Mock embedding service."""
    with patch("app.services.embedding.EmbeddingService.get_model") as mock:
        import numpy as np
        model = MagicMock()
        model.encode.return_value = np.random.rand(384).astype('float32')
        mock.return_value = model
        yield mock


@pytest.fixture
def mock_llm():
    """Mock LLM service."""
    with patch("app.services.llm_service.httpx.AsyncClient") as mock:
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = [{"generated_text": "AI generated response"}]
        mock.return_value.__aenter__.return_value.post = AsyncMock(return_value=response)
        yield mock
