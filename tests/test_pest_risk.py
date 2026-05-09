import pytest

def test_get_supported_crops_pest(client):
    """Test the list of supported crops for pest risk"""
    response = client.get("/api/v1/pest/crops")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "supported_crops" in data
    assert "risk_levels" in data

@pytest.mark.asyncio
async def test_assess_pest_risk_valid(client):
    """Test pest risk assessment with valid data"""
    payload = {
        "crop": "Cotton",
        "state": "Maharashtra",
        "district": "Pune",
        "growth_stage": "Vegetative",
        "latitude": 18.5,
        "longitude": 73.8
    }
    
    response = client.post("/api/v1/pest/assess", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "success" in data
    assert "pest_risks" in data
    assert "risk_timeline_7_days" in data
    assert "preventive_measures" in data

@pytest.mark.asyncio
async def test_assess_pest_risk_invalid(client):
    """Test pest risk assessment with missing required data"""
    payload = {
        "crop": "Cotton"
        # missing state and growth_stage
    }
    
    response = client.post("/api/v1/pest/assess", json=payload)
    assert response.status_code == 422
