import pytest

from app.models.database import AsyncSessionLocal
from app.services.geo_service import geo_service


@pytest.mark.asyncio
async def test_find_nearby_locations():
    """Test finding nearby locations"""
    async with AsyncSessionLocal() as db:
        locations = await geo_service.find_nearby_locations(
            db=db, latitude=37.5665, longitude=126.9780, radius_km=5.0
        )
        assert isinstance(locations, list)


@pytest.mark.asyncio
async def test_create_location():
    """Test creating a new location"""
    async with AsyncSessionLocal() as db:
        location = await geo_service.create_location(
            db=db,
            name="테스트 장소",
            latitude=37.5665,
            longitude=126.9780,
            category="test",
        )
        assert location.name == "테스트 장소"
        assert location.category == "test"
