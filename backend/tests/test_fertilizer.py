import pytest


def test_get_fertilizer_products(client):
    """Test the list of available fertilizer products"""
    response = client.get("/api/v1/fertilizer/products")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "products" in data
    assert "total_count" in data
    # products could be a dict or a list depending on implementation

@pytest.mark.asyncio
async def test_recommend_fertilizer_valid(client):
    """Test fertilizer recommendation with valid data"""
    payload = {
        "crop": "wheat",
        "ph": 6.5,
        "nitrogen": 45,
        "phosphorus": 20,
        "potassium": 30,
        "area_hectares": 1.5
    }

    response = client.post("/api/v1/fertilizer/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "success" in data
    assert "npk_analysis" in data
    assert "recommended_products" in data
    assert isinstance(data["recommendations"], list)

@pytest.mark.asyncio
async def test_recommend_fertilizer_invalid_data(client):
    """Test fertilizer recommendation with missing data"""
    # Missing required N, P, K
    payload = {
        "crop": "wheat",
        "area_hectares": 1.5
    }

    response = client.post("/api/v1/fertilizer/recommend", json=payload)
    assert response.status_code == 422
