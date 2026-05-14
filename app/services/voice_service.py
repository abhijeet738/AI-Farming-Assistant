"""
Voice Service — Speech-to-Text (faster-whisper) + Text-to-Speech (edge-tts)

Provides:
    - transcribe_audio(): Convert farmer's spoken audio → text
    - text_to_speech(): Convert agent response text → MP3 audio
    - Auto language detection (Hindi / English)
"""

import asyncio
import io
import os
import tempfile

import edge_tts
import structlog
from pydub import AudioSegment

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Whisper model (loaded lazily on first use to avoid slow startup)
# ---------------------------------------------------------------------------
_whisper_model = None
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small")


def _get_whisper_model():
    """Lazy-load the faster-whisper model on first transcription request."""
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel

        logger.info(
            "Loading Whisper STT model...",
            model_size=WHISPER_MODEL_SIZE,
        )
        _whisper_model = WhisperModel(
            WHISPER_MODEL_SIZE,
            device="cpu",
            compute_type="int8",  # Fastest on CPU
        )
        logger.info("✅ Whisper STT model loaded successfully")
    return _whisper_model


# ---------------------------------------------------------------------------
# TTS Voice Mapping
# ---------------------------------------------------------------------------
TTS_VOICES = {
    "hi": "hi-IN-SwaraNeural",      # Hindi female (natural)
    "en": "en-IN-NeerjaNeural",      # English-India female
    "hi-male": "hi-IN-MadhurNeural", # Hindi male
    "en-male": "en-IN-PrabhatNeural", # English-India male
}

# Maximum audio constraints
MAX_AUDIO_DURATION_SECONDS = 60
MAX_AUDIO_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


# ---------------------------------------------------------------------------
# Speech-to-Text
# ---------------------------------------------------------------------------
async def transcribe_audio(
    audio_bytes: bytes,
    language: str | None = None,
) -> dict:
    """
    Transcribe audio bytes to text using faster-whisper.

    Args:
        audio_bytes: Raw audio file bytes (WAV, MP3, WebM, etc.)
        language: Optional language hint ("hi" for Hindi, "en" for English).
                  If None, auto-detects the language.

    Returns:
        dict with keys: transcript, language, confidence, duration_seconds
    """
    if len(audio_bytes) > MAX_AUDIO_FILE_SIZE_BYTES:
        raise ValueError(
            f"Audio file too large ({len(audio_bytes) / 1024 / 1024:.1f} MB). "
            f"Maximum allowed: {MAX_AUDIO_FILE_SIZE_BYTES / 1024 / 1024:.0f} MB."
        )

    # Convert any audio format to WAV using pydub (requires ffmpeg)
    try:
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
    except Exception as e:
        raise ValueError(f"Unsupported or corrupted audio format: {e}")

    duration_seconds = len(audio) / 1000.0
    if duration_seconds > MAX_AUDIO_DURATION_SECONDS:
        raise ValueError(
            f"Audio too long ({duration_seconds:.0f}s). "
            f"Maximum allowed: {MAX_AUDIO_DURATION_SECONDS}s."
        )

    # Export to WAV in a temp file for Whisper
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        audio.export(tmp.name, format="wav")
        tmp_path = tmp.name

    try:
        # Run transcription in a thread to avoid blocking the event loop
        model = _get_whisper_model()

        def _transcribe():
            segments, info = model.transcribe(
                tmp_path,
                language=language,
                beam_size=5,
                vad_filter=True,  # Skip silence for faster processing
            )
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())
            return " ".join(text_parts), info

        loop = asyncio.get_event_loop()
        transcript, info = await loop.run_in_executor(None, _transcribe)

        detected_language = info.language if info.language else (language or "en")
        confidence = round(info.language_probability, 3) if info.language_probability else 0.0

        logger.info(
            "Audio transcribed successfully",
            language=detected_language,
            confidence=confidence,
            duration=round(duration_seconds, 1),
            transcript_length=len(transcript),
        )

        return {
            "transcript": transcript,
            "language": detected_language,
            "confidence": confidence,
            "duration_seconds": round(duration_seconds, 1),
        }
    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Text-to-Speech
# ---------------------------------------------------------------------------
async def text_to_speech(
    text: str,
    language: str = "en",
    voice: str | None = None,
) -> bytes:
    """
    Convert text to speech using edge-tts.

    Args:
        text: The text to synthesize.
        language: Language code ("hi" for Hindi, "en" for English).
        voice: Optional specific voice name override.

    Returns:
        MP3 audio bytes.
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty for TTS.")

    # Select voice based on language
    selected_voice = voice or TTS_VOICES.get(language, TTS_VOICES["en"])

    logger.info(
        "Generating TTS audio",
        voice=selected_voice,
        text_length=len(text),
    )

    # edge-tts generates audio
    communicate = edge_tts.Communicate(text=text, voice=selected_voice)

    # Collect audio bytes
    audio_chunks = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])

    if not audio_chunks:
        raise RuntimeError("TTS engine returned no audio data.")

    audio_bytes = b"".join(audio_chunks)

    logger.info(
        "TTS audio generated successfully",
        voice=selected_voice,
        audio_size_kb=round(len(audio_bytes) / 1024, 1),
    )

    return audio_bytes
