import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.url_service import url_service

logger = logging.getLogger(__name__)

router = APIRouter()


class URLCreateRequest(BaseModel):
    url: str
    custom_code: str = None
    expires_in_days: int = 30


class URLResponse(BaseModel):
    short_url: str
    original_url: str
    short_code: str


class URLStatsResponse(BaseModel):
    short_code: str
    original_url: str
    click_count: int
    created_at: str


@router.post("/create", response_model=URLResponse)
async def create_short_url(request: URLCreateRequest) -> URLResponse:
    """단축 URL 생성"""
    logger.info(f"Creating short URL for: {request.url}")

    try:
        short_url = await url_service.create_short_url(
            original_url=request.url,
            short_code=request.custom_code,
            expires_in_days=request.expires_in_days,
        )

        # short_code 추출
        short_code = short_url.split("/")[-1]

        logger.info(f"Successfully created short URL: {short_url}")

        return URLResponse(
            short_url=short_url, original_url=request.url, short_code=short_code
        )

    except Exception as e:
        logger.error(f"Error creating short URL: {str(e)}")
        raise HTTPException(
            status_code=500, detail="단축 URL 생성 중 오류가 발생했습니다"
        ) from e


@router.get("/stats/{short_code}", response_model=URLStatsResponse)
async def get_url_stats(short_code: str) -> URLStatsResponse:
    """URL 통계 조회"""
    logger.info(f"Getting stats for short code: {short_code}")

    try:
        stats = await url_service.get_url_stats(short_code)
        if not stats:
            logger.warning(f"No stats found for short code: {short_code}")
            raise HTTPException(status_code=404, detail="통계를 찾을 수 없습니다")

        logger.info(f"Retrieved stats for {short_code}: {stats['click_count']} clicks")

        return URLStatsResponse(
            short_code=short_code,
            original_url=stats["original_url"],
            click_count=stats["click_count"],
            created_at=stats["created_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting URL stats: {str(e)}")
        raise HTTPException(
            status_code=500, detail="통계 조회 중 오류가 발생했습니다"
        ) from e


@router.get("/list")
async def list_all_urls() -> dict[str, Any]:
    """모든 단축 URL 목록 조회"""
    logger.info("Retrieving all short URLs")

    try:
        urls = await url_service.get_all_urls()
        logger.info(f"Found {len(urls)} short URLs")

        return {"count": len(urls), "urls": urls}

    except Exception as e:
        logger.error(f"Error listing URLs: {str(e)}")
        raise HTTPException(
            status_code=500, detail="URL 목록 조회 중 오류가 발생했습니다"
        ) from e


@router.delete("/{short_code}")
async def delete_short_url(short_code: str) -> dict[str, str]:
    """단축 URL 삭제"""
    logger.info(f"Deleting short URL: {short_code}")

    try:
        success = await url_service.delete_short_url(short_code)
        if not success:
            logger.warning(f"Failed to delete short URL: {short_code}")
            raise HTTPException(status_code=404, detail="단축 URL을 찾을 수 없습니다")

        logger.info(f"Successfully deleted short URL: {short_code}")
        return {"message": "단축 URL이 성공적으로 삭제되었습니다"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting short URL: {str(e)}")
        raise HTTPException(
            status_code=500, detail="단축 URL 삭제 중 오류가 발생했습니다"
        ) from e


@router.get("/health")
async def health_check():
    """URL 서비스 상태 확인"""
    logger.debug("URL service health check requested")
    return {"status": "healthy", "service": "url_shortener"}
