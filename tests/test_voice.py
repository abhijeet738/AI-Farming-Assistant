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
