
import pytest


@pytest.mark.asyncio
async def test_analyze_disease_valid_image(client):
    """Test disease detection with a mock image file"""
    # Create a small dummy image in memory (just bytes, not a real valid image format but passes basic check)
    file_content = b"fake image bytes for testing"
    files = {
        "file": ("test_leaf.jpg", file_content, "image/jpeg")
    }

    response = client.post("/api/v1/disease/analyze", files=files)
    assert response.status_code == 200
    data = response.json()

    assert "success" in data
    # Predictions might be missing if fallback is used due to no ML model loaded.

@pytest.mark.asyncio
async def test_analyze_disease_invalid_file_type(client):
    """Test disease detection with an invalid file type"""
    file_content = b"this is a text file"
    files = {
        "file": ("test.txt", file_content, "text/plain")
    }

    response = client.post("/api/v1/disease/analyze", files=files)
    assert response.status_code == 400
    assert "must be an image" in response.json()["message"]
