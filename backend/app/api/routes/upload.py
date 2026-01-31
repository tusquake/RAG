import os
import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, BackgroundTasks
from typing import Optional

from app.config import get_settings
from app.models.document import DocumentType, DocumentStatus, DocumentResponse
from app.db.mongodb import get_collection
from app.api.middleware.auth import get_current_user
from app.api.middleware.rate_limiter import moderate_rate_limit
from app.services.document_processor import process_document_sync

settings = get_settings()
router = APIRouter()


def get_document_type(filename: str) -> Optional[DocumentType]:
    ext = os.path.splitext(filename)[1].lower()
    
    if ext in settings.ALLOWED_PDF_EXTENSIONS:
        return DocumentType.PDF
    elif ext in settings.ALLOWED_AUDIO_EXTENSIONS:
        return DocumentType.AUDIO
    elif ext in settings.ALLOWED_VIDEO_EXTENSIONS:
        return DocumentType.VIDEO
    
    return None


def validate_file_size(file_size: int) -> bool:
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    return file_size <= max_size


@router.post("/pdf", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(moderate_rate_limit)
):
    return await _upload_file(
        file, 
        DocumentType.PDF, 
        settings.ALLOWED_PDF_EXTENSIONS,
        current_user,
        background_tasks
    )


@router.post("/audio", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(moderate_rate_limit)
):
    return await _upload_file(
        file,
        DocumentType.AUDIO,
        settings.ALLOWED_AUDIO_EXTENSIONS,
        current_user,
        background_tasks
    )


@router.post("/video", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(moderate_rate_limit)
):
    return await _upload_file(
        file,
        DocumentType.VIDEO,
        settings.ALLOWED_VIDEO_EXTENSIONS,
        current_user,
        background_tasks
    )


async def _upload_file(
    file: UploadFile,
    expected_type: DocumentType,
    allowed_extensions: list,
    current_user: dict,
    background_tasks: BackgroundTasks
) -> DocumentResponse:
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    content = await file.read()
    file_size = len(content)
    
    if not validate_file_size(file_size):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum of {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    unique_id = str(uuid.uuid4())
    filename = f"{unique_id}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)
    
    doc = {
        "filename": filename,
        "original_filename": file.filename,
        "document_type": expected_type.value,
        "file_path": file_path,
        "file_size": file_size,
        "user_id": current_user["id"],
        "status": DocumentStatus.PENDING.value,
        "text_content": None,
        "summary": None,
        "duration": None,
        "timestamps": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "processing_error": None
    }
    
    documents_collection = get_collection("documents")
    result = await documents_collection.insert_one(doc)
    doc_id = str(result.inserted_id)
    
    background_tasks.add_task(process_document_sync, doc_id, file_path, expected_type)
    
    return DocumentResponse(
        id=doc_id,
        filename=filename,
        original_filename=file.filename,
        document_type=expected_type,
        file_size=file_size,
        status=DocumentStatus.PENDING,
        created_at=doc["created_at"]
    )
