import os
from typing import Dict, List

from app.config import get_settings

settings = get_settings()


class PDFProcessor:
    async def extract_text(self, file_path: str) -> Dict:
        import asyncio
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._extract_sync, file_path)
        return result
    
    def _extract_sync(self, file_path: str) -> Dict:
        import fitz
        
        doc = fitz.open(file_path)
        
        text_content = []
        pages = []
        
        for page_num, page in enumerate(doc):
            page_text = page.get_text()
            text_content.append(page_text)
            pages.append({
                "page_number": page_num + 1,
                "text": page_text,
                "char_count": len(page_text)
            })
        
        metadata = doc.metadata or {}
        doc.close()
        
        full_text = "\n\n".join(text_content).strip()
        
        if len(full_text) < 50:
            print(f"Text too short ({len(full_text)} chars), attempting OCR for {file_path}")
            return self._extract_ocr(file_path, metadata)
        
        return {
            "text": full_text,
            "pages": pages,
            "page_count": len(pages),
            "char_count": len(full_text),
            "word_count": len(full_text.split()),
            "metadata": {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "creator": metadata.get("creator", "")
            }
        }
        
    def _extract_ocr(self, file_path: str, metadata: Dict) -> Dict:
        import pytesseract
        from pdf2image import convert_from_path
        
        try:
            images = convert_from_path(file_path)
            
            text_content = []
            pages = []
            
            for i, image in enumerate(images):
                page_text = pytesseract.image_to_string(image)
                text_content.append(page_text)
                
                pages.append({
                    "page_number": i + 1,
                    "text": page_text,
                    "char_count": len(page_text)
                })
                
            full_text = "\n\n".join(text_content)
            
            return {
                "text": full_text,
                "pages": pages,
                "page_count": len(pages),
                "char_count": len(full_text),
                "word_count": len(full_text.split()),
                "metadata": {
                    "title": metadata.get("title", ""),
                    "author": metadata.get("author", ""),
                    "subject": metadata.get("subject", ""),
                    "creator": metadata.get("creator", "")
                }
            }
        except Exception as e:
            print(f"OCR failed: {e}")
            return {
                "text": "",
                "pages": [],
                "page_count": 0,
                "char_count": 0,
                "word_count": 0,
                "metadata": metadata,
                "error": str(e)
            }
    
    def chunk_text(
        self,
        text: str,
        chunk_size: int = None,
        overlap: int = None
    ) -> List[Dict]:
        chunk_size = chunk_size or settings.CHUNK_SIZE
        overlap = overlap or settings.CHUNK_OVERLAP
        
        if len(text) <= chunk_size:
            return [{"text": text, "start": 0, "end": len(text)}]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            if end < len(text):
                for punct in ['. ', '! ', '? ', '\n\n', '\n']:
                    last_punct = text.rfind(punct, start, end)
                    if last_punct > start:
                        end = last_punct + len(punct)
                        break
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "start": start,
                    "end": end,
                    "index": len(chunks)
                })
            
            start = end - overlap
            
            if start >= len(text):
                break
        
        return chunks
