"""Models package initialization."""
from app.models.user import UserCreate, UserLogin, UserResponse, UserInDB, Token, TokenData
from app.models.document import (
    DocumentType, DocumentStatus, TimestampSegment,
    DocumentCreate, DocumentInDB, DocumentResponse, DocumentListResponse
)
from app.models.chat import (
    ChatMessage, ChatRequest, ChatResponse, ChatHistoryInDB,
    ChatHistoryResponse, SummarizeRequest, SummarizeResponse,
    TimestampQuery, TimestampResponse
)

__all__ = [
    # User models
    "UserCreate", "UserLogin", "UserResponse", "UserInDB", "Token", "TokenData",
    # Document models
    "DocumentType", "DocumentStatus", "TimestampSegment",
    "DocumentCreate", "DocumentInDB", "DocumentResponse", "DocumentListResponse",
    # Chat models
    "ChatMessage", "ChatRequest", "ChatResponse", "ChatHistoryInDB",
    "ChatHistoryResponse", "SummarizeRequest", "SummarizeResponse",
    "TimestampQuery", "TimestampResponse"
]
