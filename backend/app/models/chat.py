from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sources: Optional[List[dict]] = []


class ChatRequest(BaseModel):
    message: str
    document_id: str
    stream: bool = False


class ChatResponse(BaseModel):
    message: str
    sources: List[dict] = []
    timestamps: Optional[List[dict]] = []


class ChatHistoryInDB(BaseModel):
    document_id: str
    user_id: str
    messages: List[ChatMessage] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ChatHistoryResponse(BaseModel):
    id: str
    document_id: str
    messages: List[ChatMessage]
    created_at: datetime


class SummarizeRequest(BaseModel):
    document_id: str
    max_length: Optional[int] = 500


class SummarizeResponse(BaseModel):
    document_id: str
    summary: str
    word_count: int


class TimestampQuery(BaseModel):
    document_id: str
    query: str


class TimestampResponse(BaseModel):
    document_id: str
    query: str
    timestamps: List[dict]
