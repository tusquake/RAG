from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    PDF = "pdf"
    AUDIO = "audio"
    VIDEO = "video"


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TimestampSegment(BaseModel):
    start: float
    end: float
    text: str
    topic: Optional[str] = None


class DocumentCreate(BaseModel):
    filename: str
    document_type: DocumentType
    file_path: str
    user_id: str


class DocumentInDB(BaseModel):
    filename: str
    original_filename: str
    document_type: DocumentType
    file_path: str
    file_size: int
    user_id: str
    status: DocumentStatus = DocumentStatus.PENDING
    
    text_content: Optional[str] = None
    summary: Optional[str] = None
    
    duration: Optional[float] = None
    timestamps: Optional[List[TimestampSegment]] = []
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    processing_error: Optional[str] = None


class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    document_type: DocumentType
    file_size: int
    status: DocumentStatus
    summary: Optional[str] = None
    duration: Optional[float] = None
    timestamps: Optional[List[TimestampSegment]] = []
    created_at: datetime
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int
