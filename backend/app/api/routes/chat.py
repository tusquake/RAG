import json
from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import StreamingResponse
from datetime import datetime
from bson import ObjectId
from typing import Optional

from app.config import get_settings
from app.models.chat import (
    ChatRequest, ChatResponse, ChatHistoryResponse,
    SummarizeRequest, SummarizeResponse,
    TimestampQuery, TimestampResponse, ChatMessage
)
from app.models.document import DocumentStatus
from app.db.mongodb import get_collection
from app.api.middleware.auth import get_current_user
from app.api.middleware.rate_limiter import moderate_rate_limit
from app.services.rag_pipeline import RAGPipeline
from app.services.llm_service import LLMService

settings = get_settings()
router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(moderate_rate_limit)
):
    documents_collection = get_collection("documents")
    
    if not ObjectId.is_valid(request.document_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID"
        )
    
    doc = await documents_collection.find_one({
        "_id": ObjectId(request.document_id),
        "user_id": current_user["id"]
    })
    
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if doc["status"] != DocumentStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document is not ready. Status: {doc['status']}"
        )
    
    rag = RAGPipeline()
    
    context_chunks = await rag.retrieve_context(
        request.document_id,
        request.message
    )
    
    llm = LLMService()
    response_text, sources = await llm.generate_response(
        question=request.message,
        context_chunks=context_chunks,
        document_type=doc["document_type"]
    )
    
    timestamps = []
    if doc["document_type"] in ["audio", "video"] and doc.get("timestamps"):
        timestamps = await rag.find_relevant_timestamps(
            request.message,
            doc.get("timestamps", [])
        )
    
    chat_collection = get_collection("chat_history")
    
    user_message = ChatMessage(
        role="user",
        content=request.message,
        timestamp=datetime.utcnow()
    )
    
    assistant_message = ChatMessage(
        role="assistant",
        content=response_text,
        timestamp=datetime.utcnow(),
        sources=sources
    )
    
    await chat_collection.update_one(
        {
            "document_id": request.document_id,
            "user_id": current_user["id"]
        },
        {
            "$push": {
                "messages": {
                    "$each": [
                        user_message.model_dump(),
                        assistant_message.model_dump()
                    ]
                }
            },
            "$set": {"updated_at": datetime.utcnow()},
            "$setOnInsert": {"created_at": datetime.utcnow()}
        },
        upsert=True
    )
    
    return ChatResponse(
        message=response_text,
        sources=sources,
        timestamps=timestamps
    )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(moderate_rate_limit)
):
    documents_collection = get_collection("documents")
    
    if not ObjectId.is_valid(request.document_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID"
        )
    
    doc = await documents_collection.find_one({
        "_id": ObjectId(request.document_id),
        "user_id": current_user["id"]
    })
    
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if doc["status"] != DocumentStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document is not ready. Status: {doc['status']}"
        )
    
    rag = RAGPipeline()
    
    context_chunks = await rag.retrieve_context(
        request.document_id,
        request.message
    )
    
    llm = LLMService()
    
    async def generate():
        full_response = ""
        async for chunk in llm.generate_response_stream(
            question=request.message,
            context_chunks=context_chunks,
            document_type=doc["document_type"]
        ):
            full_response += chunk
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        
        timestamps = []
        if doc["document_type"] in ["audio", "video"] and doc.get("timestamps"):
            timestamps = await rag.find_relevant_timestamps(
                request.message,
                doc.get("timestamps", [])
            )
        
        yield f"data: {json.dumps({'done': True, 'timestamps': timestamps})}\n\n"
        
        chat_collection = get_collection("chat_history")
        await chat_collection.update_one(
            {
                "document_id": request.document_id,
                "user_id": current_user["id"]
            },
            {
                "$push": {
                    "messages": {
                        "$each": [
                            {"role": "user", "content": request.message, "timestamp": datetime.utcnow()},
                            {"role": "assistant", "content": full_response, "timestamp": datetime.utcnow()}
                        ]
                    }
                },
                "$set": {"updated_at": datetime.utcnow()},
                "$setOnInsert": {"created_at": datetime.utcnow()}
            },
            upsert=True
        )
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


@router.get("/history/{document_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(moderate_rate_limit)
):
    chat_collection = get_collection("chat_history")
    
    if not ObjectId.is_valid(document_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID"
        )
    
    history = await chat_collection.find_one({
        "document_id": document_id,
        "user_id": current_user["id"]
    })
    
    if not history:
        return ChatHistoryResponse(
            id="",
            document_id=document_id,
            messages=[],
            created_at=datetime.utcnow()
        )
    
    return ChatHistoryResponse(
        id=str(history["_id"]),
        document_id=document_id,
        messages=[ChatMessage(**msg) for msg in history.get("messages", [])],
        created_at=history.get("created_at", datetime.utcnow())
    )


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_document(
    request: SummarizeRequest,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(moderate_rate_limit)
):
    documents_collection = get_collection("documents")
    
    if not ObjectId.is_valid(request.document_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID"
        )
    
    doc = await documents_collection.find_one({
        "_id": ObjectId(request.document_id),
        "user_id": current_user["id"]
    })
    
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if doc["status"] != DocumentStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document is not ready. Status: {doc['status']}"
        )
    
    if doc.get("summary"):
        return SummarizeResponse(
            document_id=request.document_id,
            summary=doc["summary"],
            word_count=len(doc["summary"].split())
        )
    
    llm = LLMService()
    summary = await llm.generate_summary(
        text=doc.get("text_content", ""),
        max_length=request.max_length
    )
    
    await documents_collection.update_one(
        {"_id": ObjectId(request.document_id)},
        {"$set": {"summary": summary, "updated_at": datetime.utcnow()}}
    )
    
    return SummarizeResponse(
        document_id=request.document_id,
        summary=summary,
        word_count=len(summary.split())
    )


@router.post("/timestamps", response_model=TimestampResponse)
async def find_timestamps(
    request: TimestampQuery,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(moderate_rate_limit)
):
    documents_collection = get_collection("documents")
    
    if not ObjectId.is_valid(request.document_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID"
        )
    
    doc = await documents_collection.find_one({
        "_id": ObjectId(request.document_id),
        "user_id": current_user["id"]
    })
    
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if doc["document_type"] not in ["audio", "video"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Timestamps are only available for audio/video files"
        )
    
    if doc["status"] != DocumentStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document is not ready. Status: {doc['status']}"
        )
    
    rag = RAGPipeline()
    timestamps = await rag.find_relevant_timestamps(
        request.query,
        doc.get("timestamps", [])
    )
    
    return TimestampResponse(
        document_id=request.document_id,
        query=request.query,
        timestamps=timestamps
    )
