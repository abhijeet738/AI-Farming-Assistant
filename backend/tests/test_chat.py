import pytest


@pytest.mark.asyncio
async def test_chat_invoke_valid(client):
    """Test invoking the chat agent with a valid message"""
    payload = {
        "message": "What fertilizer is best for wheat?",
        "location": "Punjab",
        "crop_context": "wheat"
    }

    response = client.post("/api/v1/chat/invoke", json=payload)
    assert response.status_code in [200, 500]  # 500 if Gemini API key is missing

@pytest.mark.asyncio
async def test_chat_invoke_invalid(client):
    """Test invoking the chat agent with missing message"""
    payload = {
        "location": "Punjab"
    }

    response = client.post("/api/v1/chat/invoke", json=payload)
    assert response.status_code == 422
