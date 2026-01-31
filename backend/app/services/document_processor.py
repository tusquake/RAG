import asyncio
import sys
from datetime import datetime
from bson import ObjectId

from app.models.document import DocumentType, DocumentStatus
from app.db.mongodb import get_collection
from app.services.pdf_processor import PDFProcessor
from app.services.transcription import TranscriptionService
from app.services.rag_pipeline import RAGPipeline


def process_document_sync(
    document_id: str,
    file_path: str,
    document_type: DocumentType
):
    print(f"[BACKGROUND] Starting processing for document {document_id}", flush=True)
    try:
        asyncio.run(_process_document_async(document_id, file_path, document_type))
        print(f"[BACKGROUND] Completed processing for document {document_id}", flush=True)
    except Exception as e:
        print(f"[BACKGROUND] Fatal error processing document {document_id}: {e}", flush=True)
        import traceback
        traceback.print_exc()


async def _process_document_async(
    document_id: str,
    file_path: str,
    document_type: DocumentType
):
    documents_collection = get_collection("documents")
    
    try:
        await documents_collection.update_one(
            {"_id": ObjectId(document_id)},
            {
                "$set": {
                    "status": DocumentStatus.PROCESSING.value,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if document_type == DocumentType.PDF:
            result = await _process_pdf(document_id, file_path)
        elif document_type == DocumentType.AUDIO:
            result = await _process_audio(document_id, file_path)
        elif document_type == DocumentType.VIDEO:
            result = await _process_video(document_id, file_path)
        else:
            raise ValueError(f"Unknown document type: {document_type}")
        
        await documents_collection.update_one(
            {"_id": ObjectId(document_id)},
            {
                "$set": {
                    "status": DocumentStatus.COMPLETED.value,
                    "text_content": result.get("text", ""),
                    "duration": result.get("duration"),
                    "timestamps": result.get("timestamps", []),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        print(f"Document {document_id} processed successfully", flush=True)
        
    except Exception as e:
        print(f"Error processing document {document_id}: {e}", flush=True)
        import traceback
        traceback.print_exc()
        
        await documents_collection.update_one(
            {"_id": ObjectId(document_id)},
            {
                "$set": {
                    "status": DocumentStatus.FAILED.value,
                    "processing_error": str(e),
                    "updated_at": datetime.utcnow()
                }
            }
        )


async def _process_pdf(document_id: str, file_path: str) -> dict:
    print(f"[PDF] Starting PDF processing for {document_id}", flush=True)
    processor = PDFProcessor()
    rag = RAGPipeline()
    
    print(f"[PDF] Extracting text from {file_path}", flush=True)
    result = await processor.extract_text(file_path)
    print(f"[PDF] Extracted {len(result.get('text', ''))} characters", flush=True)
    
    chunks = processor.chunk_text(result["text"])
    print(f"[PDF] Created {len(chunks)} chunks for indexing", flush=True)
    
    print(f"[PDF] Indexing chunks in vector store...", flush=True)
    await rag.index_document(document_id, chunks)
    print(f"[PDF] Indexing complete for {document_id}", flush=True)
    
    return {
        "text": result["text"],
        "duration": None,
        "timestamps": []
    }


async def _process_audio(document_id: str, file_path: str) -> dict:
    transcription = TranscriptionService()
    rag = RAGPipeline()
    pdf_processor = PDFProcessor()
    
    result = await transcription.transcribe_audio(file_path)
    
    topics = transcription.extract_topics(result["segments"])
    
    chunks = pdf_processor.chunk_text(result["text"])
    
    for chunk in chunks:
        for segment in result["segments"]:
            if segment["text"] in chunk["text"]:
                chunk["start_time"] = segment["start"]
                chunk["end_time"] = segment["end"]
                break
    
    await rag.index_document(document_id, chunks)
    
    return {
        "text": result["text"],
        "duration": result["duration"],
        "timestamps": topics
    }


async def _process_video(document_id: str, file_path: str) -> dict:
    transcription = TranscriptionService()
    rag = RAGPipeline()
    pdf_processor = PDFProcessor()
    
    result = await transcription.transcribe_video(file_path)
    
    topics = transcription.extract_topics(result["segments"])
    
    chunks = pdf_processor.chunk_text(result["text"])
    
    for chunk in chunks:
        for segment in result["segments"]:
            if segment["text"] in chunk["text"]:
                chunk["start_time"] = segment["start"]
                chunk["end_time"] = segment["end"]
                break
    
    await rag.index_document(document_id, chunks)
    
    return {
        "text": result["text"],
        "duration": result["duration"],
        "timestamps": topics
    }
