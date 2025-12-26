"""
TTS services - modularized from the original tts_service.py
"""
from pathlib import Path
from typing import Dict, List, Optional

from .audio_generator import AudioGenerator
from .ppt_embedder import PPTEmbedder
from .notes_sync import NotesSync

class TTSService:
    """
    Unified TTS service facade.
    Coordinates audio generation, PPT embedding, and notes synchronization.
    """
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.audio_gen = AudioGenerator(output_dir)
        self.ppt_embedder = PPTEmbedder(output_dir)
        self.notes_sync = NotesSync()
    
    async def list_voices(self, language: str = None) -> List[Dict]:
        """List available TTS voices"""
        return await self.audio_gen.list_voices(language)
    
    async def generate_audio(
        self, 
        text: str, 
        voice: str, 
        rate: str = "+0%", 
        pitch: str = "+0Hz"
    ) -> Dict:
        """Generate audio from text"""
        return await self.audio_gen.generate_audio(text, voice, rate, pitch)
    
    async def generate_narrated_pptx(
        self,
        original_pptx_path: str,
        slide_scripts: List[Dict],
        voice: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        progress_callback: Optional[callable] = None,
    ) -> Dict:
        """
        Generate narrated PPT with audio and notes.
        
        Args:
            original_pptx_path: Path to original PPT
            slide_scripts: List of slide script data
            voice: TTS voice
            rate: Speech rate
            pitch: Speech pitch
            progress_callback: Progress callback function
            
        Returns:
            Dict with filename, path, and url_path
        """
        # Embed audio
        output_path, all_slide_scripts = await self.ppt_embedder.embed_audio(
            original_pptx_path,
            slide_scripts,
            self.audio_gen,
            voice,
            rate,
            pitch,
            progress_callback
        )
        
        # Sync notes
        if progress_callback:
            progress_callback(90, "Synchronizing slide notes...")
        
        try:
            self.notes_sync.sync_notes(output_path, all_slide_scripts)
        except Exception as e:
            print(f"[TTSService] Notes sync failed: {e}")
        
        # Return result
        output_filename = Path(output_path).name
        return {
            "filename": output_filename,
            "path": output_path,
            "url_path": f"/outputs/{output_filename}"
        }

__all__ = ['TTSService', 'AudioGenerator', 'PPTEmbedder', 'NotesSync']
