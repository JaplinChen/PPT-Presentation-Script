from .schemas import (
    ErrorResponse,
    GenerateScriptRequest,
    GenerateScriptResponse,
    NarratedPPTRequest,
    PPTUploadResponse,
    SlideData,
    SlideScriptItem,
    TranslateRequest,
    TTSGenerateRequest,
    TTSGenerateResponse,
    TTSVoiceResponse,
    ParseStatusResponse,
    NarratedPPTStatusResponse,
)

# Backward compatibility imports
from pydantic import BaseModel, Field  # noqa: F401
from typing import Any, Dict, List, Optional  # noqa: F401
