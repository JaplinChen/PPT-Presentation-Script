"""
Audio generation using Edge TTS.
"""
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import edge_tts

class AudioGenerator:
    """Handles TTS audio generation using Edge TTS"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def list_voices(self, language: str = None) -> List[Dict]:
        """
        List available voices, optionally filtered by language.
        
        Args:
            language: Language prefix filter (e.g., 'zh', 'en')
            
        Returns:
            List of voice dictionaries
        """
        voices = await edge_tts.list_voices()
        
        result = []
        for v in voices:
            if language and not v['Locale'].startswith(language):
                continue
                
            result.append({
                "short_name": v['ShortName'],
                "friendly_name": v['FriendlyName'],
                "gender": v['Gender'],
                "locale": v['Locale']
            })
            
        return result
    
    async def generate_audio(
        self, 
        text: str, 
        voice: str, 
        rate: str = "+0%", 
        pitch: str = "+0Hz"
    ) -> Dict:
        """
        Generate audio file from text.
        
        Args:
            text: Text to convert to speech
            voice: Voice name
            rate: Speech rate adjustment
            pitch: Pitch adjustment
            
        Returns:
            Dict with filename, path, and url_path
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")

        filename = f"{uuid.uuid4()}.mp3"
        output_path = self.output_dir / filename

        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        await communicate.save(str(output_path))

        return {
            "filename": filename,
            "path": str(output_path),
            "url_path": f"/outputs/{filename}"
        }
