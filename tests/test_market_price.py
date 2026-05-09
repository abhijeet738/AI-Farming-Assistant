import pytest

def test_get_supported_crops_market(client):
    """Test the list of supported crops for market prices"""
    response = client.get("/api/v1/market/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "supported_crops" in data
    assert "total_count" in data
    assert len(data["supported_crops"]) > 0

@pytest.mark.asyncio
async def test_get_market_price_valid(client):
    """Test market price fetching for a valid crop"""
    response = client.get("/api/v1/market/Rice?state=Maharashtra")
    assert response.status_code == 200
    data = response.json()
    
    assert "success" in data
    assert data["crop"].lower() == "rice"
    assert "current_price_per_quintal" in data
    assert "currency" in data
    assert "forecast_7_days" in data

@pytest.mark.asyncio
async def test_get_market_price_invalid_crop(client):
    """Test market price fetching for an unknown crop"""
    response = client.get("/api/v1/market/unknown_crop_123")
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is False
