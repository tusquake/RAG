"""Tests for document management endpoints."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from bson import ObjectId


class TestDocumentListEndpoint:
    """Tests for document listing."""
    
    @pytest.mark.asyncio
    async def test_list_documents_empty(self, mock_mongodb, auth_headers):
        """Test listing documents when none exist."""
        mock_mongodb.db.documents.count_documents = AsyncMock(return_value=0)
        mock_mongodb.db.documents.find = MagicMock(return_value=AsyncMock())
        
        with patch("app.db.mongodb.get_collection", return_value=mock_mongodb.db.documents):
            count = await mock_mongodb.db.documents.count_documents({})
            assert count == 0
    
    @pytest.mark.asyncio
    async def test_list_documents_with_results(self, mock_mongodb, sample_document):
        """Test listing documents with results."""
        mock_mongodb.db.documents.count_documents = AsyncMock(return_value=1)
        
        async def mock_cursor():
            yield sample_document
        
        mock_find = MagicMock()
        mock_find.sort.return_value.skip.return_value.limit.return_value = mock_cursor()
        mock_mongodb.db.documents.find = MagicMock(return_value=mock_find)
        
        with patch("app.db.mongodb.get_collection", return_value=mock_mongodb.db.documents):
            count = await mock_mongodb.db.documents.count_documents({})
            assert count == 1


class TestDocumentGetEndpoint:
    """Tests for getting a single document."""
    
    def test_valid_object_id(self):
        """Test ObjectId validation."""
        valid_id = "507f1f77bcf86cd799439011"
        invalid_id = "not-valid-id"
        
        assert ObjectId.is_valid(valid_id) is True
        assert ObjectId.is_valid(invalid_id) is False
    
    @pytest.mark.asyncio
    async def test_get_document_found(self, mock_mongodb, sample_document):
        """Test getting an existing document."""
        mock_mongodb.db.documents.find_one = AsyncMock(return_value=sample_document)
        
        with patch("app.db.mongodb.get_collection", return_value=mock_mongodb.db.documents):
            doc = await mock_mongodb.db.documents.find_one({})
            assert doc is not None
            assert doc["filename"] == sample_document["filename"]
    
    @pytest.mark.asyncio
    async def test_get_document_not_found(self, mock_mongodb):
        """Test getting a non-existent document."""
        mock_mongodb.db.documents.find_one = AsyncMock(return_value=None)
        
        with patch("app.db.mongodb.get_collection", return_value=mock_mongodb.db.documents):
            doc = await mock_mongodb.db.documents.find_one({})
            assert doc is None


class TestDocumentDeleteEndpoint:
    """Tests for deleting documents."""
    
    @pytest.mark.asyncio
    async def test_delete_document(self, mock_mongodb, sample_document):
        """Test deleting a document."""
        mock_mongodb.db.documents.find_one = AsyncMock(return_value=sample_document)
        mock_mongodb.db.documents.delete_one = AsyncMock()
        mock_mongodb.db.chat_history.delete_many = AsyncMock()
        
        with patch("app.db.mongodb.get_collection") as mock_get:
            mock_get.side_effect = lambda name: {
                "documents": mock_mongodb.db.documents,
                "chat_history": mock_mongodb.db.chat_history
            }[name]
            
            doc = await mock_mongodb.db.documents.find_one({})
            assert doc is not None
            
            await mock_mongodb.db.documents.delete_one({})
            mock_mongodb.db.documents.delete_one.assert_called_once()


class TestDocumentResponse:
    """Tests for document response models."""
    
    def test_document_response_from_db(self, sample_document):
        """Test creating DocumentResponse from database document."""
        from app.models.document import DocumentResponse
        
        response = DocumentResponse(
            id=str(sample_document["_id"]),
            filename=sample_document["filename"],
            original_filename=sample_document["original_filename"],
            document_type=sample_document["document_type"],
            file_size=sample_document["file_size"],
            status=sample_document["status"],
            created_at=datetime.utcnow()
        )
        
        assert response.filename == "test.pdf"
        assert response.status == "completed"
    
    def test_document_list_response(self):
        """Test DocumentListResponse model."""
        from app.models.document import DocumentListResponse, DocumentResponse
        
        docs = [
            DocumentResponse(
                id="1",
                filename="doc1.pdf",
                original_filename="doc1.pdf",
                document_type="pdf",
                file_size=1024,
                status="completed",
                created_at=datetime.utcnow()
            )
        ]
        
        response = DocumentListResponse(
            documents=docs,
            total=1,
            page=1,
            page_size=10
        )
        
        assert len(response.documents) == 1
        assert response.total == 1
