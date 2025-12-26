"""
Main script generator that coordinates all script generation functionality.
"""
from pathlib import Path
from typing import Dict, List, Optional

from .gemini_provider import GeminiProvider, QuotaExceededError
from .parser import ScriptParser

class ScriptGenerator:
    """
    Generate and translate presentation scripts using AI.
    Coordinates Gemini provider and script parser.
    """
    
    # Re-export exception for backward compatibility
    QuotaExceededError = QuotaExceededError
    
    def __init__(self, api_key: Optional[str] = None, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)
        self.gemini = GeminiProvider(api_key)
        self.parser = ScriptParser()
    
    def generate_full_script(
        self,
        slides: List[Dict],
        audience: str = "General audience",
        purpose: str = "Introduce the topic",
        context: str = "Formal meeting",
        tone: str = "Professional and natural",
        duration_sec: int = 300,
        include_transitions: bool = True,
        language: str = "Traditional Chinese",
        provider: str = "gemini",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> Dict:
        """
        Generate a full presentation script.
        
        Args:
            slides: List of slide data with titles and bullets
            audience: Target audience description
            purpose: Presentation purpose
            context: Presentation context
            tone: Desired tone
            duration_sec: Target duration in seconds
            include_transitions: Whether to include transitions
            language: Target language
            provider: AI provider (currently only 'gemini' supported)
            model: Model override (unused, for compatibility)
            api_key: API key override (unused, for compatibility)
            
        Returns:
            Dict with 'opening', 'slides', and 'full_script' keys
        """
        # Build prompt
        prompt = self._build_generation_prompt(
            slides, audience, purpose, context, tone, 
            duration_sec, include_transitions, language
        )
        
        # Generate script
        full_script = self.gemini.generate(prompt)
        
        # Parse into structured format
        result = self.parser.parse_script(full_script, slides, include_transitions)
        
        return result
    
    def translate_and_parse(
        self, 
        full_script: str, 
        target_language: str, 
        api_key: Optional[str] = None
    ) -> str:
        """
        Translate a script to target language.
        
        Args:
            full_script: The script to translate
            target_language: Target language name
            api_key: API key override (unused, for compatibility)
            
        Returns:
            Translated script text
        """
        return self.gemini.translate(full_script, target_language)
    
    def _build_generation_prompt(
        self,
        slides: List[Dict],
        audience: str,
        purpose: str,
        context: str,
        tone: str,
        duration_sec: int,
        include_transitions: bool,
        language: str
    ) -> str:
        """Build the prompt for script generation"""
        
        # Format slides for prompt
        slides_text = self._format_slides(slides)
        
        # Calculate timing
        total_slides = len(slides)
        avg_time_per_slide = duration_sec / total_slides if total_slides > 0 else 30
        
        # Build prompt
        prompt = f"""
You are a professional presentation script writer.

Generate a complete presentation script in {language} based on the following slides.

**Presentation Details:**
- Audience: {audience}
- Purpose: {purpose}
- Context: {context}
- Tone: {tone}
- Total Duration: {duration_sec} seconds (~{int(duration_sec/60)} minutes)
- Average time per slide: ~{int(avg_time_per_slide)} seconds

**Slides Content:**
{slides_text}

**Instructions:**
1. Write a brief opening (30-60 seconds) to introduce the presentation
2. For each slide, write a natural script that:
   - Explains the key points clearly
   - Uses the specified tone
   - Takes approximately {int(avg_time_per_slide)} seconds to read
   {"- Includes smooth transitions between slides" if include_transitions else ""}
3. Use clear section markers:
   - "=== Opening ===" for the introduction
   - "--- Slide X ---" for each slide (where X is the slide number)

**Output Format:**
=== Opening ===
[Your opening script here]

--- Slide 1 ---
[Script for slide 1]

--- Slide 2 ---
[Script for slide 2]

... and so on for all slides.

Generate the complete script now:
"""
        return prompt
    
    def _format_slides(self, slides: List[Dict]) -> str:
        """Format slides for inclusion in prompt"""
        formatted = []
        
        for slide in slides:
            slide_no = slide.get("slide_no", 0)
            title = slide.get("title", "")
            bullets = slide.get("bullets", [])
            
            slide_text = f"Slide {slide_no}: {title}\n"
            if bullets:
                for bullet in bullets:
                    slide_text += f"  - {bullet}\n"
            
            formatted.append(slide_text)
        
        return "\n".join(formatted)
    
    def _load_prompt(self, filename: str) -> str:
        """Load prompt template from file (for future use)"""
        prompt_path = self.prompts_dir / filename
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        return ""
