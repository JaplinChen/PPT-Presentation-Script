"""
Script parser for converting generated text into structured format.
"""
import re
from typing import Dict, List

class ScriptParser:
    """Parses generated scripts into structured slide-by-slide format"""
    
    @staticmethod
    def parse_script(full_script: str, slides: List[Dict], include_transitions: bool = True) -> Dict:
        """
        Parse generated script text into structured format.
        
        Args:
            full_script: The full generated script text
            slides: Original slide data for reference
            include_transitions: Whether transitions were included
            
        Returns:
            Dict with 'opening', 'slides', and 'full_script' keys
        """
        # Extract sections using markers
        sections = ScriptParser._extract_sections(full_script)
        
        # Parse opening
        opening = ""
        if sections and "opening" in sections[0].lower():
            opening = sections[0].split("\n", 1)[1].strip() if "\n" in sections[0] else ""
        
        # Parse slide sections
        slide_scripts = []
        for i, slide in enumerate(slides):
            slide_no = slide.get("slide_no", i + 1)
            
            # Find matching section
            script_text = ScriptParser._find_slide_script(sections, slide_no)
            
            if not script_text:
                script_text = f"(Slide {slide_no} - No script generated)"
            
            # Split into sentences for segments
            segments = ScriptParser._split_into_segments(script_text)
            
            slide_scripts.append({
                "slide_no": str(slide_no),  # Convert to string for API model
                "title": slide.get("title", ""),
                "script": script_text,
                "segments": segments
            })
        
        return {
            "opening": opening,
            "slide_scripts": slide_scripts,
            "full_script": full_script,
            "metadata": {
                "total_slides": len(slides),
                "has_opening": bool(opening),
                "parser_version": "2.0"
            }
        }
    
    @staticmethod
    def _extract_sections(text: str) -> List[str]:
        """
        Extract sections from script text using markers.
        Looks for patterns like "--- Slide X ---" or "==="
        """
        # Split by slide markers
        pattern = r'(?:^|\n)(?:---|===).*?(?:Slide|投影片)\s*(\d+).*?(?:---|===)'
        parts = re.split(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Clean up sections
        sections = []
        for part in parts:
            cleaned = part.strip()
            if cleaned and len(cleaned) > 10:  # Filter out very short sections
                sections.append(cleaned)
        
        return sections if sections else [text]
    
    @staticmethod
    def _find_slide_script(sections: List[str], slide_no: int) -> str:
        """Find the script section for a specific slide number"""
        # Try to find section mentioning this slide number
        for section in sections:
            if f"slide {slide_no}" in section.lower() or f"投影片 {slide_no}" in section.lower():
                # Remove the header line
                lines = section.split("\n")
                return "\n".join(lines[1:]).strip() if len(lines) > 1 else section
        
        # Fallback: use section by index if available
        if 0 <= slide_no - 1 < len(sections):
            return sections[slide_no - 1]
        
        return ""
    
    @staticmethod
    def _split_into_segments(text: str) -> List[Dict]:
        """
        Split script text into sentence segments.
        Each segment represents a logical speaking unit.
        """
        if not text:
            return []
        
        # Split by sentence endings
        sentences = re.split(r'([。！？.!?])', text)
        
        segments = []
        current = ""
        
        for i, part in enumerate(sentences):
            current += part
            
            # If this is a sentence ending, create a segment
            if part in '。！？.!?':
                cleaned = current.strip()
                if cleaned and len(cleaned) > 2:
                    segments.append({
                        "text": cleaned,
                        "type": "content"
                    })
                current = ""
        
        # Add any remaining text
        if current.strip():
            segments.append({
                "text": current.strip(),
                "type": "content"
            })
        
        return segments if segments else [{"text": text, "type": "content"}]
