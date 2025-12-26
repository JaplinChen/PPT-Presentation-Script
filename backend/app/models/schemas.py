from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SlideData(BaseModel):
    """Parsed slide content."""

    slide_no: int
    title: str
    bullets: List[str] = Field(default_factory=list)
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    notes: str = ""
    image_count: int = 0


class GenerateScriptRequest(BaseModel):
    """Request body for script generation."""

    audience: str = Field(default="General audience", description="Target audience")
    purpose: str = Field(default="Introduce the topic", description="Presentation purpose")
    context: str = Field(default="Formal meeting", description="Presentation context")
    tone: str = Field(default="Professional and natural", description="Voice and tone")
    duration_sec: int = Field(default=300, description="Desired duration in seconds")
    include_transitions: bool = Field(default=True, description="Include slide transitions")
    language: str = Field(
        default="Traditional Chinese", description="Output language (display string)"
    )
    provider: str = Field(default="gemini", description="LLM provider: gemini or openai")
    model: Optional[str] = Field(default=None, description="Optional model name per provider")
    api_key: Optional[str] = Field(
        default=None, description="Optional Gemini API key supplied by the user"
    )


class TranslateRequest(BaseModel):
    """Request body for translating a full script."""

    full_script: str = Field(..., description="Complete presentation script")
    target_language: str = Field(..., description="Language to translate into")
    api_key: Optional[str] = Field(
        default=None, description="Optional Gemini API key supplied by the user"
    )


class SlideScriptItem(BaseModel):
    """Script content for a single slide."""

    slide_no: str
    title: str
    script: str
    segments: Optional[List[Dict[str, Any]]] = None


class GenerateScriptResponse(BaseModel):
    """Response body for generated scripts."""

    opening: str
    slide_scripts: List[SlideScriptItem]
    full_script: str
    metadata: Dict[str, Any]


class PPTUploadResponse(BaseModel):
    """Result of a PPT upload and parse."""

    success: bool
    message: str
    file_id: str
    slides: List[SlideData]
    summary: Dict[str, Any]


class ErrorResponse(BaseModel):
    """Standard error payload."""

    success: bool = False
    error: str
    detail: Optional[str] = None


class TTSVoiceResponse(BaseModel):
    """A single TTS voice option."""

    short_name: str
    friendly_name: str
    gender: str
    locale: str


class TTSGenerateRequest(BaseModel):
    """Request to synthesize audio."""

    text: str
    voice: str
    rate: str = "+0%"
    pitch: str = "+0Hz"


class TTSGenerateResponse(BaseModel):
    """Response for synthesized audio."""

    filename: str
    path: str
    url_path: str


class NarratedPPTRequest(BaseModel):
    """Request to produce a narrated PPTX."""

    file_id: str
    slide_scripts: List[Dict[str, Any]]
    voice: str
    rate: str = "+0%"
    pitch: str = "+0Hz"


class ParseStatusResponse(BaseModel):
    """Status of background PPT parsing."""

    file_id: str
    status: str  # pending, processing, completed, failed
    progress: int
    message: str
    slides: Optional[List[SlideData]] = None
    summary: Optional[Dict[str, Any]] = None


class NarratedPPTStatusResponse(BaseModel):
    """Status of background narrated PPT generation."""

    job_id: str
    file_id: str
    status: str  # pending, processing, completed, failed
    progress: int
    message: str
    result: Optional[TTSGenerateResponse] = None
