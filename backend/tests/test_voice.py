"""Tests for Voice Interface endpoints."""

import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_voice_speak_valid(client, monkeypatch):
    """Test TTS endpoint with valid text."""

    async def _fake_tts(text: str, language: str = "en", voice: str | None = None) -> bytes:
        return b"fake-mp3-bytes"

    monkeypatch.setattr("app.api.v1.voice.text_to_speech", _fake_tts)

    response = client.post(
        "/api/v1/voice/speak",
        json={"text": "Hello farmer, your wheat crop is looking healthy!", "language": "en"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/mpeg")
    assert response.content == b"fake-mp3-bytes"

def test_voice_speak_empty_text(client):
    """Test TTS endpoint rejects empty text"""
    response = client.post(
        "/api/v1/voice/speak",
        json={"text": "", "language": "en"},
    )
    assert response.status_code == 400


def test_voice_transcribe_invalid_file(client):
    """Test STT endpoint rejects non-audio files"""
    response = client.post(
        "/api/v1/voice/transcribe",
        files={"file": ("test.txt", b"This is not audio", "text/plain")},
    )
    assert response.status_code == 400


def test_voice_chat_happy_path(client, monkeypatch):
    """Test full voice pipeline endpoint with mocked STT/agent/TTS."""

    async def _fake_transcribe(audio_bytes: bytes, language: str | None = None) -> dict:
        return {
            "transcript": "Hello",
            "language": "en",
            "confidence": 1.0,
            "duration_seconds": 1.0,
        }

    async def _fake_tts(text: str, language: str = "en", voice: str | None = None) -> bytes:
        return b"fake-mp3"

    class _Msg:
        def __init__(self, content: str):
            self.content = content
            self.tool_calls = []

    class _DummyGraph:
        async def ainvoke(self, input_state, config=None):
            return {"messages": [_Msg("Hi there")]}

    async def _noop_seed():
        return None

    monkeypatch.setattr("app.api.v1.voice.transcribe_audio", _fake_transcribe)
    monkeypatch.setattr("app.api.v1.voice.text_to_speech", _fake_tts)
    monkeypatch.setattr("app.agent.graph.ensure_knowledge_seeded", _noop_seed)
    monkeypatch.setattr("app.agent.graph.graph", _DummyGraph())

    response = client.post(
        "/api/v1/voice/chat",
        files={"file": ("q.wav", b"00", "audio/wav")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["transcript"] == "Hello"
    assert body["agent_response"] == "Hi there"
    assert body["audio_base64"]
