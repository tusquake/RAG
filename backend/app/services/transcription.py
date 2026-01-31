import os
import tempfile
from typing import List, Dict, Optional
import subprocess

from app.config import get_settings

settings = get_settings()


class TranscriptionService:
    def __init__(self):
        self.model = None
        self.model_name = settings.WHISPER_MODEL
    
    def _load_model(self):
        if self.model is None:
            import whisper
            self.model = whisper.load_model(self.model_name)
        return self.model
    
    async def transcribe_audio(self, file_path: str) -> Dict:
        import asyncio
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._transcribe_sync, file_path)
        return result
    
    def _transcribe_sync(self, file_path: str) -> Dict:
        model = self._load_model()
        
        result = model.transcribe(
            file_path,
            word_timestamps=True,
            verbose=False
        )
        
        segments = []
        for segment in result.get("segments", []):
            segments.append({
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"].strip()
            })
        
        duration = segments[-1]["end"] if segments else 0
        
        return {
            "text": result["text"],
            "segments": segments,
            "duration": duration,
            "language": result.get("language", "en")
        }
    
    async def transcribe_video(self, file_path: str) -> Dict:
        audio_path = await self._extract_audio(file_path)
        
        try:
            result = await self.transcribe_audio(audio_path)
            return result
        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)
    
    async def _extract_audio(self, video_path: str) -> str:
        import asyncio
        
        temp_dir = tempfile.gettempdir()
        audio_path = os.path.join(temp_dir, f"audio_{os.path.basename(video_path)}.wav")
        
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            "-y",
            audio_path
        ]
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: subprocess.run(cmd, capture_output=True, check=True)
        )
        
        return audio_path
    
    def extract_topics(self, segments: List[Dict]) -> List[Dict]:
        if not segments:
            return []
        
        topics = []
        current_topic = {
            "start": segments[0]["start"],
            "end": segments[0]["end"],
            "text": segments[0]["text"]
        }
        
        for i, segment in enumerate(segments[1:], 1):
            if i % 5 == 0:
                topics.append(current_topic)
                current_topic = {
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"]
                }
            else:
                current_topic["end"] = segment["end"]
                current_topic["text"] += " " + segment["text"]
        
        if current_topic["text"]:
            topics.append(current_topic)
        
        return topics
