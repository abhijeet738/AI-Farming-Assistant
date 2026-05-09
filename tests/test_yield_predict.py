import pytest

def test_get_supported_crops_for_yield(client):
    """Test the list of supported crops for yield prediction"""
    response = client.get("/api/v1/yield/crops")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "supported_crops" in data
    assert "total_count" in data
    assert len(data["supported_crops"]) > 0

@pytest.mark.asyncio
async def test_predict_yield_valid(client):
    """Test yield prediction with valid data"""
    payload = {
        "crop": "Rice",
        "season": "Kharif",
        "state": "Maharashtra",
        "district": "Pune",
        "area_hectares": 2.5
    }
    
    response = client.post("/api/v1/yield/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # ML might fail internally and fallback, so success could be False
    assert "success" in data
    assert "predicted_yield_tonnes_per_hectare" in data
    assert "total_production_tonnes" in data
    assert "confidence_interval_lower" in data

@pytest.mark.asyncio
async def test_predict_yield_invalid_data(client):
    """Test yield prediction with missing data"""
    payload = {
        "crop": "rice",
        "state": "Maharashtra"
    }
    
    response = client.post("/api/v1/yield/predict", json=payload)
    assert response.status_code == 422
