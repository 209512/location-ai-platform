import pytest

from app.services.url_service import url_service


@pytest.mark.asyncio
async def test_create_short_url():
    """Test creating short URL"""
    original_url = "https://example.com/very/long/url"
    short_url = await url_service.create_short_url(original_url)

    assert short_url.startswith("http://localhost:8000/s/")
    assert len(short_url) > len(original_url)


@pytest.mark.asyncio
async def test_get_original_url():
    """Test retrieving original URL"""
    original_url = "https://example.com/test"
    short_url = await url_service.create_short_url(original_url)
    short_code = short_url.split("/")[-1]

    retrieved_url = await url_service.get_original_url(short_code)
    assert retrieved_url == original_url


@pytest.mark.asyncio
async def test_url_stats():
    """Test URL statistics"""
    original_url = "https://example.com/stats-test"
    short_url = await url_service.create_short_url(original_url)
    short_code = short_url.split("/")[-1]

    # Simulate a click
    await url_service.get_original_url(short_code)

    stats = await url_service.get_url_stats(short_code)
    assert stats is not None
    assert stats["click_count"] >= 1
