"""
Gemini API provider for script generation.
"""
import os
import google.generativeai as genai
from typing import Dict, List, Optional

class QuotaExceededError(Exception):
    """Raised when Gemini responds with a quota/429 error."""
    pass

class GeminiProvider:
    """Handles Gemini API interactions for script generation"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        genai.configure(api_key=self.api_key)
        self.model_name = "gemini-flash-latest"
        self.model = genai.GenerativeModel(self.model_name)
    
    def generate(self, prompt: str) -> str:
        """
        Generate content using Gemini API.
        
        Args:
            prompt: The prompt to send to Gemini
            
        Returns:
            Generated text response
            
        Raises:
            QuotaExceededError: If API quota is exceeded
        """
        try:
            response = self.model.generate_content(prompt)
            
            if not response or not hasattr(response, "text"):
                raise ValueError("Empty response from Gemini")
            
            return response.text
            
        except Exception as e:
            error_msg = str(e).lower()
            if "quota" in error_msg or "429" in error_msg:
                raise QuotaExceededError(f"Gemini API quota exceeded: {e}")
            raise
    
    def translate(self, text: str, target_language: str) -> str:
        """
        Translate text to target language.
        
        Args:
            text: Text to translate
            target_language: Target language name
            
        Returns:
            Translated text
        """
        prompt = f"""
Translate the following presentation script to {target_language}.
Preserve all formatting markers (e.g., "--- Slide X ---", "===").
Keep the structure exactly the same.

Original text:
{text}

Translated text:
"""
        return self.generate(prompt)
