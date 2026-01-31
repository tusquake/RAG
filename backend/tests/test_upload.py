"""Tests for file upload endpoints."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO
from bson import ObjectId


class TestUploadEndpoints:
    """Tests for file upload functionality."""
    
    def test_get_document_type_pdf(self):
        """Test PDF type detection."""
        from app.api.routes.upload import get_document_type
        from app.models.document import DocumentType
        
        assert get_document_type("document.pdf") == DocumentType.PDF
        assert get_document_type("DOCUMENT.PDF") == DocumentType.PDF
    
    def test_get_document_type_audio(self):
        """Test audio type detection."""
        from app.api.routes.upload import get_document_type
        from app.models.document import DocumentType
        
        assert get_document_type("audio.mp3") == DocumentType.AUDIO
        assert get_document_type("audio.wav") == DocumentType.AUDIO
        assert get_document_type("audio.m4a") == DocumentType.AUDIO
        assert get_document_type("audio.flac") == DocumentType.AUDIO
    
    def test_get_document_type_video(self):
        """Test video type detection."""
        from app.api.routes.upload import get_document_type
        from app.models.document import DocumentType
        
        assert get_document_type("video.mp4") == DocumentType.VIDEO
        assert get_document_type("video.webm") == DocumentType.VIDEO
        assert get_document_type("video.mkv") == DocumentType.VIDEO
    
    def test_get_document_type_unknown(self):
        """Test unknown type returns None."""
        from app.api.routes.upload import get_document_type
        
        assert get_document_type("file.txt") is None
        assert get_document_type("file.doc") is None
        assert get_document_type("file") is None
    
    def test_validate_file_size_valid(self):
        """Test valid file size."""
        from app.api.routes.upload import validate_file_size
        
        # 10 MB should be valid
        assert validate_file_size(10 * 1024 * 1024) is True
        
        # 50 MB should be valid
        assert validate_file_size(50 * 1024 * 1024) is True
    
    def test_validate_file_size_invalid(self):
        """Test invalid file size."""
        from app.api.routes.upload import validate_file_size
        
        # 150 MB should be invalid (max is 100MB)
        assert validate_file_size(150 * 1024 * 1024) is False


class TestDocumentModels:
    """Tests for document models."""
    
    def test_document_status_enum(self):
        """Test document status values."""
        from app.models.document import DocumentStatus
        
        assert DocumentStatus.PENDING.value == "pending"
        assert DocumentStatus.PROCESSING.value == "processing"
        assert DocumentStatus.COMPLETED.value == "completed"
        assert DocumentStatus.FAILED.value == "failed"
    
    def test_document_type_enum(self):
        """Test document type values."""
        from app.models.document import DocumentType
        
        assert DocumentType.PDF.value == "pdf"
        assert DocumentType.AUDIO.value == "audio"
        assert DocumentType.VIDEO.value == "video"
    
    def test_timestamp_segment_model(self):
        """Test timestamp segment creation."""
        from app.models.document import TimestampSegment
        
        segment = TimestampSegment(
            start=0.0,
            end=30.5,
            text="Introduction",
            topic="intro"
        )
        
        assert segment.start == 0.0
        assert segment.end == 30.5
        assert segment.text == "Introduction"
        assert segment.topic == "intro"
