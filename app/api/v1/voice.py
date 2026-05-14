"""
Voice API Router — STT, TTS, and full voice-to-voice chat.

Endpoints:
    POST /api/v1/voice/transcribe  — Audio → Text (STT only)
    POST /api/v1/voice/speak       — Text → Audio (TTS only)
    POST /api/v1/voice/chat        — Audio → Agent → Audio (full pipeline)
"""

import base64

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.core.rate_limit import limiter
from app.services.voice_service import text_to_speech, transcribe_audio

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------
class TTSRequest(BaseModel):
    """Request body for text-to-speech."""
    text: str = Field(..., description="Text to convert to speech", max_length=5000)
    language: str = Field("en", description="Language code: 'hi' (Hindi) or 'en' (English)")
    voice: str | None = Field(None, description="Optional specific voice name override")


class TranscriptionResponse(BaseModel):
    """Response from speech-to-text."""
    success: bool = True
    transcript: str
    language: str
    confidence: float
    duration_seconds: float


class VoiceChatResponse(BaseModel):
    """Response from the full voice chat pipeline."""
    success: bool = True
    transcript: str
    detected_language: str
    agent_response: str
    audio_base64: str = Field(
        ..., description="Base64-encoded MP3 audio of the agent's spoken response"
    )


# ---------------------------------------------------------------------------
# 1. Speech-to-Text Only
# ---------------------------------------------------------------------------
@router.post("/transcribe", response_model=TranscriptionResponse)
@limiter.limit("30/minute")
async def voice_transcribe(
    request: Request,
    file: UploadFile = File(..., description="Audio file (WAV, MP3, WebM, M4A)"),
    language: str | None = None,
):
    """
    Upload an audio recording and get the transcribed text.

    Accepts: WAV, MP3, WebM, M4A, OGG
    Automatically detects Hindi or English if no language is specified.
    """
    if not file.content_type or not (
        file.content_type.startswith("audio/")
        or file.content_type in ("video/webm", "application/octet-stream")
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Send an audio file.",
        )

    try:
        audio_bytes = await file.read()
        result = await transcribe_audio(audio_bytes, language=language)
        return TranscriptionResponse(
            transcript=result["transcript"],
            language=result["language"],
            confidence=result["confidence"],
            duration_seconds=result["duration_seconds"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}",
        )


# ---------------------------------------------------------------------------
# 2. Text-to-Speech Only
# ---------------------------------------------------------------------------
@router.post("/speak")
@limiter.limit("30/minute")
async def voice_speak(request: Request, payload: TTSRequest):
    """
    Convert text to natural-sounding speech.

    Returns an MP3 audio file directly.
    Supports Hindi (`hi`) and English (`en`) voices.
    """
    try:
        audio_bytes = await text_to_speech(
            text=payload.text,
            language=payload.language,
            voice=payload.voice,
        )
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=response.mp3",
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"TTS generation failed: {str(e)}",
        )


# ---------------------------------------------------------------------------
# 3. Full Voice Chat Pipeline (STT → Agent → TTS)
# ---------------------------------------------------------------------------
@router.post("/chat", response_model=VoiceChatResponse)
@limiter.limit("15/minute")
async def voice_chat(
    request: Request,
    file: UploadFile = File(..., description="Audio file with the farmer's question"),
    location: str | None = None,
    crop_context: str | None = None,
):
    """
    Full voice-to-voice conversation with the farming AI agent.

    1. Transcribes the farmer's audio (auto-detects Hindi/English)
    2. Sends the text to the LangGraph farming agent
    3. Converts the agent's response to speech
    4. Returns both text and audio (base64-encoded MP3)
    """
    # --- Step 1: Transcribe audio ---
    try:
        audio_bytes = await file.read()
        stt_result = await transcribe_audio(audio_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Speech recognition failed: {str(e)}",
        )

    transcript = stt_result["transcript"]
    detected_lang = stt_result["language"]

    if not transcript.strip():
        raise HTTPException(
            status_code=400,
            detail="Could not understand the audio. Please speak clearly and try again.",
        )

    # --- Step 2: Send to LangGraph agent ---
    try:
        from app.agent.graph import ensure_knowledge_seeded, graph

        await ensure_knowledge_seeded()

        config = {"configurable": {"thread_id": "voice-default"}}
        input_state = {
            "messages": [{"role": "user", "content": transcript}],
            "location": location or "",
            "crop_context": crop_context or "",
        }

        result = await graph.ainvoke(input_state, config=config)

        # Extract the last AI message
        agent_response = ""
        for msg in reversed(result.get("messages", [])):
            if hasattr(msg, "content") and msg.content:
                if not hasattr(msg, "tool_calls") or not msg.tool_calls:
                    agent_response = msg.content
                    break

        if not agent_response:
            agent_response = "I'm sorry, I couldn't process your request. Please try again."

    except Exception as e:
        # If agent fails, still return the transcript with an error response
        agent_response = (
            "I'm having trouble connecting to the farming knowledge base right now. "
            "Please try again in a moment."
        )

    # --- Step 3: Convert response to speech ---
    try:
        tts_audio = await text_to_speech(
            text=agent_response,
            language=detected_lang,
        )
        audio_b64 = base64.b64encode(tts_audio).decode("utf-8")
    except Exception:
        audio_b64 = ""  # Return text response even if TTS fails

    return VoiceChatResponse(
        transcript=transcript,
        detected_language=detected_lang,
        agent_response=agent_response,
        audio_base64=audio_b64,
    )
