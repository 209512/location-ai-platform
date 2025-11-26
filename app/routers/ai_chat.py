import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.services.ai_service import ai_service
from app.services.url_service import url_service

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    latitude: float
    longitude: float
    category: str = "general"


class ChatResponse(BaseModel):
    response: str
    share_url: str


@router.post("/recommend", response_model=ChatResponse)
async def get_ai_recommendation(request: ChatRequest) -> ChatResponse:
    """위치 기반 AI 추천 생성"""
    logger.info(f"Received AI recommendation request: {request.message}")
    logger.debug(f"Location: {request.latitude}, {request.longitude}")

    try:
        # AI 서비스로 추천 생성
        ai_response = await ai_service.get_location_recommendations(
            latitude=request.latitude,
            longitude=request.longitude,
            query=request.message,
        )

        # 단축 URL 생성
        share_url = await url_service.create_short_url(
            original_url=f"{settings.base_url}/share/recommendation", expires_in_days=7
        )

        logger.info("Successfully generated AI recommendation with share URL")

        return ChatResponse(response=ai_response, share_url=share_url)

    except Exception as e:
        logger.error(f"Error generating AI recommendation: {str(e)}")
        raise HTTPException(
            status_code=500, detail="추천 생성 중 오류가 발생했습니다"
        ) from e


@router.get("/health")
async def health_check():
    """AI 챗봇 서비스 상태 확인"""
    logger.debug("AI chat health check requested")
    return {"status": "healthy", "service": "ai_chat"}
