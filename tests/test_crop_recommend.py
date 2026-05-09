import pytest

def test_get_supported_crops(client):
    """Test the list of supported crops"""
    response = client.get("/api/v1/crop/list")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "crops" in data
    assert "total_count" in data
    assert isinstance(data["crops"], list)
    assert len(data["crops"]) > 0

@pytest.mark.asyncio
async def test_recommend_crops_valid(client):
    """Test crop recommendation with valid data"""
    payload = {
        "nitrogen": 90,
        "phosphorus": 42,
        "potassium": 43,
        "temperature": 20.8,
        "humidity": 82.0,
        "ph": 6.5,
        "rainfall": 202.9,
        "soil_type": "Loamy",
        "latitude": 19.0,
        "longitude": 73.0
    }
    
    response = client.post("/api/v1/crop/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "success" in data
    assert "recommendations" in data
    assert len(data["recommendations"]) > 0

@pytest.mark.asyncio
async def test_recommend_crops_invalid_data(client):
    """Test crop recommendation with missing/invalid data"""
    # Missing required 'nitrogen' field
    payload = {
        "phosphorus": 42,
        "potassium": 43,
        "temperature": 20.8,
        "humidity": 82.0,
        "ph": 6.5,
        "rainfall": 202.9,
        "soil_type": "loamy"
    }
    
    response = client.post("/api/v1/crop/recommend", json=payload)
    assert response.status_code == 422  # FastAPI validation error
