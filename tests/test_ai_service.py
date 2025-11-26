import pytest

from app.services.ai_service import ai_service


@pytest.mark.asyncio
async def test_ai_service_recommendations():
    """Test AI service recommendations"""
    response = await ai_service.get_location_recommendations(
        latitude=37.5665, longitude=126.9780, query="맛집 추천해줘"
    )
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_ai_service_with_category():
    """Test AI service with category filter"""
    response = await ai_service.get_location_recommendations(
        latitude=37.5665, longitude=126.9780, query="카페", category="cafe"
    )
    assert isinstance(response, str)
    assert "카페" in response or "cafe" in response.lower()
