import os
from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import FileResponse, StreamingResponse
from typing import Optional
from bson import ObjectId

from app.config import get_settings
from app.models.document import DocumentResponse, DocumentListResponse, DocumentStatus
from app.db.mongodb import get_collection
from app.api.middleware.auth import get_current_user
from app.api.middleware.rate_limiter import relaxed_rate_limit

settings = get_settings()
router = APIRouter()


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status_filter: Optional[DocumentStatus] = None,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(relaxed_rate_limit)
):
    documents_collection = get_collection("documents")
    
    query = {"user_id": current_user["id"]}
    if status_filter:
        query["status"] = status_filter.value
    
    total = await documents_collection.count_documents(query)
    
    skip = (page - 1) * page_size
    cursor = documents_collection.find(query).sort("created_at", -1).skip(skip).limit(page_size)
    
    documents = []
    async for doc in cursor:
        documents.append(DocumentResponse(
            id=str(doc["_id"]),
            filename=doc["filename"],
            original_filename=doc["original_filename"],
            document_type=doc["document_type"],
            file_size=doc["file_size"],
            status=doc["status"],
            summary=doc.get("summary"),
            duration=doc.get("duration"),
            timestamps=doc.get("timestamps", []),
            created_at=doc["created_at"]
        ))
    
    return DocumentListResponse(
        documents=documents,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(relaxed_rate_limit)
):
    documents_collection = get_collection("documents")
    
    if not ObjectId.is_valid(document_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID"
        )
    
    doc = await documents_collection.find_one({
        "_id": ObjectId(document_id),
        "user_id": current_user["id"]
    })
    
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return DocumentResponse(
        id=str(doc["_id"]),
        filename=doc["filename"],
        original_filename=doc["original_filename"],
        document_type=doc["document_type"],
        file_size=doc["file_size"],
        status=doc["status"],
        summary=doc.get("summary"),
        duration=doc.get("duration"),
        timestamps=doc.get("timestamps", []),
        created_at=doc["created_at"]
    )


@router.get("/{document_id}/file")
async def get_document_file(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(relaxed_rate_limit)
):
    documents_collection = get_collection("documents")
    
    if not ObjectId.is_valid(document_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID"
        )
    
    doc = await documents_collection.find_one({
        "_id": ObjectId(document_id),
        "user_id": current_user["id"]
    })
    
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    file_path = doc["file_path"]
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )
    
    ext = os.path.splitext(file_path)[1].lower()
    media_types = {
        ".pdf": "application/pdf",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".m4a": "audio/mp4",
        ".flac": "audio/flac",
        ".ogg": "audio/ogg",
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".mkv": "video/x-matroska",
        ".avi": "video/x-msvideo",
        ".mov": "video/quicktime"
    }
    
    media_type = media_types.get(ext, "application/octet-stream")
    
    return FileResponse(
        path=file_path,
        filename=doc["original_filename"],
        media_type=media_type
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(relaxed_rate_limit)
):
    documents_collection = get_collection("documents")
    
    if not ObjectId.is_valid(document_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID"
        )
    
    doc = await documents_collection.find_one({
        "_id": ObjectId(document_id),
        "user_id": current_user["id"]
    })
    
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    file_path = doc["file_path"]
    if os.path.exists(file_path):
        os.remove(file_path)
    
    await documents_collection.delete_one({"_id": ObjectId(document_id)})
    
    chat_collection = get_collection("chat_history")
    await chat_collection.delete_many({"document_id": document_id})
    
    return None
