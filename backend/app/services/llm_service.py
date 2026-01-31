from typing import List, Dict, AsyncGenerator, Optional
import httpx

from app.config import get_settings

settings = get_settings()


class LLMService:
    def __init__(self):
        self.api_key = settings.HUGGINGFACE_API_KEY
        self.model = settings.HUGGINGFACE_MODEL
        self.api_url = f"https://api-inference.huggingface.co/models/{self.model}"
    
    def _get_headers(self) -> Dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _build_prompt(
        self,
        question: str,
        context_chunks: List[Dict],
        document_type: str
    ) -> str:
        context_text = "\n\n".join([
            f"[Source {i+1}]: {chunk['text']}"
            for i, chunk in enumerate(context_chunks[:5])
        ])
        
        if document_type in ["audio", "video"]:
            timestamp_info = "When relevant, reference timestamps in your answer."
        else:
            timestamp_info = ""
        
        prompt = f"""You are a helpful AI assistant answering questions about documents. Use the following context to answer the question. If you cannot find the answer in the context, say so clearly.

Context:
{context_text}

{timestamp_info}

Question: {question}

Answer: """
        
        return prompt
    
    async def generate_response(
        self,
        question: str,
        context_chunks: List[Dict],
        document_type: str = "pdf"
    ) -> tuple[str, List[Dict]]:
        prompt = self._build_prompt(question, context_chunks, document_type)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    self.api_url,
                    headers=self._get_headers(),
                    json={
                        "inputs": prompt,
                        "parameters": {
                            "max_new_tokens": 500,
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "do_sample": True,
                            "return_full_text": False
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        generated_text = result[0].get("generated_text", "")
                    else:
                        generated_text = str(result)
                else:
                    generated_text = self._generate_fallback_response(question, context_chunks)
            
            except Exception as e:
                print(f"LLM API error: {e}")
                generated_text = self._generate_fallback_response(question, context_chunks)
        
        sources = [
            {
                "text": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
                "score": chunk.get("score", 0),
                "start": chunk.get("start"),
                "end": chunk.get("end")
            }
            for chunk in context_chunks[:3]
        ]
        
        return generated_text.strip(), sources
    
    async def generate_response_stream(
        self,
        question: str,
        context_chunks: List[Dict],
        document_type: str = "pdf"
    ) -> AsyncGenerator[str, None]:
        prompt = self._build_prompt(question, context_chunks, document_type)
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.api_url,
                    headers=self._get_headers(),
                    json={
                        "inputs": prompt,
                        "parameters": {
                            "max_new_tokens": 500,
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "do_sample": True,
                            "return_full_text": False
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        text = result[0].get("generated_text", "")
                    else:
                        text = str(result)
                else:
                    text = self._generate_fallback_response(question, context_chunks)
        except Exception as e:
            print(f"LLM API error: {e}")
            text = self._generate_fallback_response(question, context_chunks)
        
        words = text.split()
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
    
    async def generate_summary(
        self,
        text: str,
        max_length: int = 500
    ) -> str:
        if len(text) > 10000:
            text = text[:10000]
        
        prompt = f"""Please provide a comprehensive summary of the following document. Focus on the key points, main topics, and important details.

Document:
{text}

Summary:"""
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    self.api_url,
                    headers=self._get_headers(),
                    json={
                        "inputs": prompt,
                        "parameters": {
                            "max_new_tokens": max_length,
                            "temperature": 0.5,
                            "top_p": 0.9,
                            "do_sample": True,
                            "return_full_text": False
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        return result[0].get("generated_text", "").strip()
                
                return self._simple_summary(text, max_length)
            
            except Exception as e:
                print(f"LLM API error: {e}")
                return self._simple_summary(text, max_length)
    
    def _generate_fallback_response(
        self,
        question: str,
        context_chunks: List[Dict]
    ) -> str:
        if not context_chunks:
            return "I couldn't find relevant information to answer your question."
        
        top_chunk = context_chunks[0]
        return f"Based on the document: {top_chunk['text'][:500]}"
    
    def _simple_summary(self, text: str, max_words: int = 100) -> str:
        sentences = text.replace('\n', ' ').split('.')
        summary_sentences = []
        word_count = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            words = len(sentence.split())
            if word_count + words > max_words:
                break
            
            summary_sentences.append(sentence)
            word_count += words
        
        return '. '.join(summary_sentences) + '.' if summary_sentences else text[:500]
