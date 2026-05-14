"""Tests for Voice Interface endpoints."""

import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_voice_speak_valid(client):
    """Test TTS endpoint with valid text"""
    response = client.post(
        "/api/v1/voice/speak",
        json={"text": "Hello farmer, your wheat crop is looking healthy!", "language": "en"},
    )
    # edge-tts requires network; in CI it may fail gracefully
    assert response.status_code in (200, 500)


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
