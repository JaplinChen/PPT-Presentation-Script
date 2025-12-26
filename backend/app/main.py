from pathlib import Path
import os
import shutil
import uuid
from typing import Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.models import (
    ErrorResponse,
    GenerateScriptRequest,
    GenerateScriptResponse,
    NarratedPPTRequest,
    PPTUploadResponse,
    TranslateRequest,
    TTSGenerateRequest,
    TTSGenerateResponse,
    ParseStatusResponse,
    NarratedPPTStatusResponse,
)
# Updated imports for modular structure
from app.config import settings
from app.utils.state_manager import state
from app.services.ppt_parser import PPTParser
from app.services.script import ScriptGenerator
from app.services.tts import TTSService

app = FastAPI(
    title="PPT Presentation Script API",
    description="Upload PPT, generate presentation scripts, translate, and synthesize narration.",
    version="1.0.0",
)

# Standard permissive CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    print(f"[GLOBAL ERROR] {request.method} {request.url}")
    print(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": str(exc), "detail": "Internal Server Error"}
    )

# Services (initialized with config)
ppt_parser = PPTParser()
script_generator: Optional[ScriptGenerator] = None
tts_service = TTSService(output_dir=settings.OUTPUT_DIR)

# Serve generated assets (audio, narrated ppt)
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")


@app.on_event("startup")
async def startup_event():
    """Initialize services that require API keys."""
    global script_generator
    if not settings.GEMINI_API_KEY:
        print("WARNING: GEMINI_API_KEY not found; generation requires per-request api_key.")
    else:
        script_generator = ScriptGenerator(api_key=settings.GEMINI_API_KEY, prompts_dir=str(settings.PROMPTS_DIR))
        print("[Init] Script generator ready.")


def ensure_generator(api_key: Optional[str] = None) -> ScriptGenerator:
    """Return a ScriptGenerator instance, preferring the global one."""
    if script_generator:
        return script_generator
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Gemini API key is required. Configure GEMINI_API_KEY or provide api_key in request.",
        )
    return ScriptGenerator(api_key=api_key, prompts_dir=str(settings.PROMPTS_DIR))


@app.get("/")
async def root():
    return {"message": "PPT Presentation Script API", "version": "1.0.0", "status": "running"}


@app.get("/api/health")
async def health_check():
    """
    Health check endpoint - does NOT call Gemini API to avoid quota issues.
    """
    return {
        "status": "healthy",
        "gemini_configured": script_generator is not None,
        "prompts_available": len(list(settings.PROMPTS_DIR.glob("*.md"))) if settings.PROMPTS_DIR.exists() else 0,
    }

@app.get("/api/ping")
async def ping():
    return {"message": "pong"}


@app.post("/api/upload", response_model=PPTUploadResponse)
def upload_ppt(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Phase 1: Upload file and return file_id immediately."""
    import time
    print(f"[API] >>> 收到上傳請求: {file.filename} (Size: {file.size if hasattr(file, 'size') else 'unknown'})")
    print(f"[API] >>> Content-Type: {file.content_type}")

    if not file.filename.lower().endswith((".ppt", ".pptx")):
        raise HTTPException(status_code=400, detail="Only .ppt and .pptx files are supported.")

    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    save_path = settings.UPLOAD_DIR / f"{file_id}{file_extension}"

    try:
        # Save file
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        state.add_uploaded_file(file_id, {
            "filename": file.filename,
            "path": str(save_path),
            "status": "pending",
            "slides": [],
            "summary": {}
        })
        state.set_parse_status(file_id, {"status": "pending", "progress": 0, "message": "Queued for parsing"})
        
        # Start background parsing
        background_tasks.add_task(background_parse_ppt, file_id, str(save_path))

        return PPTUploadResponse(
            success=True,
            message="File uploaded, parsing started in background",
            file_id=file_id,
            slides=[], # Return empty list, frontend will poll
            summary={}
        )
    except Exception as exc:
        print(f"[API] ERROR: 上傳失敗 - {exc}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(exc)}")

def background_parse_ppt(file_id: str, save_path: str):
    """CPU-bound parsing in a background thread."""
    state.set_parse_status(file_id, {"status": "processing", "progress": 10, "message": "Analyzing PPT structure..."})
    try:
        slides = ppt_parser.parse(save_path)
        
        # Text optimization removed - caused API quota issues
        # Users can manually edit scripts in the frontend
        
        summary = ppt_parser.get_summary(slides)
        
        file_data = state.get_uploaded_file(file_id)
        file_data.update({
            "slides": slides,
            "summary": summary,
            "status": "completed",
            "warnings": []
        })
        state.add_uploaded_file(file_id, file_data) # This will update the existing entry
        state.set_parse_status(file_id, {"status": "completed", "progress": 100, "message": "Analysis complete"})
    except Exception as exc:
        print(f"[Background] Analysis failed for {file_id}: {exc}")
        state.set_parse_status(file_id, {"status": "failed", "progress": 0, "message": str(exc)})

@app.get("/api/parse/{file_id}/status", response_model=ParseStatusResponse)
async def get_parse_status(file_id: str):
    """Phase 2: Poll for parsing progress."""
    status_data = state.get_parse_status(file_id)
    if not status_data:
        raise HTTPException(status_code=404, detail="File not found or parsing not started")
    
    response = {
        "file_id": file_id,
        "status": status_data["status"],
        "progress": status_data["progress"],
        "message": status_data["message"]
    }
    
    if status_data["status"] == "completed":
        file_data = state.get_uploaded_file(file_id)
        response["slides"] = file_data["slides"]
        response["summary"] = file_data["summary"]
        
    return response


@app.post("/api/generate/{file_id}", response_model=GenerateScriptResponse)
async def generate_script(file_id: str, request: GenerateScriptRequest):
    """Generate presentation script for a previously uploaded PPT."""
    print(f"[API] >>> 收到文稿生成請求: {file_id}")
    print(f"[API] >>> 參數: provider={request.provider}, model={request.model}, audience={request.audience}")
    
    file_data = state.get_uploaded_file(file_id)
    if not file_data:
        print(f"[API] ERROR: file_id {file_id} not found in uploaded_files")
        raise HTTPException(status_code=404, detail="PPT file not found.")

    current_generator = ensure_generator(request.api_key)

    # Build cache key to avoid duplicate LLM calls for same PPT + config
    cache_key = "|".join(
        [
            file_id,
            request.provider.lower(),
            request.model or "",
            request.audience,
            request.purpose,
            request.context,
            request.tone,
            str(request.duration_sec),
            str(request.include_transitions),
            request.language,
        ]
    )

    cached = state.get_generation_cache(cache_key)
    if cached:
        return GenerateScriptResponse(**cached)

    try:
        result = current_generator.generate_full_script(
            slides=file_data["slides"],
            audience=request.audience,
            purpose=request.purpose,
            context=request.context,
            tone=request.tone,
            duration_sec=request.duration_sec,
            include_transitions=request.include_transitions,
            language=request.language,
            provider=request.provider,
            model=request.model,
            api_key=request.api_key,
        )

        output_file = settings.OUTPUT_DIR / f"{file_id}_script.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result["full_script"])

        # Save to cache
        state.set_generation_cache(cache_key, result)

        return GenerateScriptResponse(**result)
    except ScriptGenerator.QuotaExceededError as exc:
        print(f"[API] ERROR: Quota exceeded - {exc}")
        raise HTTPException(status_code=429, detail=f"Gemini quota exceeded or rate limited: {exc}")
    except HTTPException:
        raise
    except Exception as exc:
        import traceback
        print(f"[API] CRITICAL ERROR during generation:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to generate script: {str(exc)}")


@app.post("/api/translate", response_model=GenerateScriptResponse)
async def translate_script(request: TranslateRequest):
    """Translate an existing script and parse it back into sections."""
    current_generator = ensure_generator(request.api_key)
    try:
        result = current_generator.translate_and_parse(
            full_script=request.full_script,
            target_language=request.target_language,
            api_key=request.api_key,
        )
        return GenerateScriptResponse(**result)
    except ScriptGenerator.QuotaExceededError as exc:
        raise HTTPException(status_code=429, detail=f"Gemini quota exceeded or rate limited: {exc}")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to translate script: {exc}")


@app.get("/api/files/{file_id}")
async def get_file_info(file_id: str):
    """Return metadata for an uploaded file."""
    file_info = state.get_uploaded_file(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found.")
    return {"file_id": file_id, "filename": file_info["filename"], "summary": file_info["summary"]}


@app.delete("/api/files/{file_id}")
async def delete_file(file_id: str):
    """Delete uploaded file and cached metadata."""
    file_data = state.get_uploaded_file(file_id)
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found.")

    file_path = Path(file_data["path"])
    if file_path.exists():
        file_path.unlink()
    
    state.delete_uploaded_file(file_id)
    # purge cached generations for this file_id
    state.clear_generation_cache_for_file(file_id)
    return {"success": True, "message": "File deleted."}


@app.get("/api/tts/voices")
async def get_tts_voices(language: Optional[str] = None):
    """List available TTS voices."""
    try:
        return await tts_service.list_voices(language)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to list voices: {exc}")


@app.post("/api/tts/generate", response_model=TTSGenerateResponse)
async def generate_tts(request: TTSGenerateRequest):
    """Generate TTS audio for provided text."""
    try:
        result = await tts_service.generate_audio(
            text=request.text, voice=request.voice, rate=request.rate, pitch=request.pitch
        )
        return TTSGenerateResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate audio: {exc}")


@app.post("/api/ppt/generate-narrated")
async def generate_narrated_ppt(request: NarratedPPTRequest, background_tasks: BackgroundTasks):
    """Generate narrated PPTX (audio embedded) as a background task."""
    if not state.get_uploaded_file(request.file_id):
        raise HTTPException(status_code=404, detail="File info not found. Please re-upload.")

    job_id = str(uuid.uuid4())
    state.add_ppt_job(job_id, {
        "job_id": job_id,
        "file_id": request.file_id,
        "status": "processing",
        "progress": 0,
        "message": "Starting narration generation...",
        "result": None,
    })

    file_data = state.get_uploaded_file(request.file_id)
    original_pptx_path = file_data["path"]

    background_tasks.add_task(
        run_narrated_pptx_task,
        job_id,
        request.file_id,
        original_pptx_path,
        request.slide_scripts,
        request.voice,
        request.rate,
        request.pitch,
    )

    return {"job_id": job_id, "status": "processing"}


@app.get("/api/ppt/job/{job_id}/status", response_model=NarratedPPTStatusResponse)
async def get_ppt_job_status(job_id: str):
    """Poll for the status of a narrated PPT generation job."""
    job_data = state.get_ppt_job(job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found.")
    return NarratedPPTStatusResponse(**job_data)


async def run_narrated_pptx_task(
    job_id: str,
    file_id: str,
    original_pptx_path: str,
    slide_scripts: List[Dict],
    voice: str,
    rate: str,
    pitch: str,
):
    """Background worker for narrated PPT generation with progress reporting."""

    def progress_callback(progress: int, message: str):
        """Update job progress"""
        if state.get_ppt_job(job_id): # Check if job still exists
            state.update_ppt_job(job_id, {
                "progress": progress,
                "message": message
            })
            print(f"[Job {job_id}] {progress}% - {message}")

    try:
        result = await tts_service.generate_narrated_pptx(
            original_pptx_path, slide_scripts, voice, rate, pitch, progress_callback=progress_callback
        )
        if state.get_ppt_job(job_id): # Check if job still exists before updating
            state.update_ppt_job(job_id, {
                "status": "completed",
                "progress": 100,
                "message": "Narrated PPT generated successfully",
                "result": result
            })
    except Exception as exc:
        import traceback

        print(f"[Job {job_id}] FAILED:")
        print(traceback.format_exc())
        if job_id in ppt_jobs:
            ppt_jobs[job_id].update({"status": "failed", "message": f"Error: {str(exc)}"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8080)
