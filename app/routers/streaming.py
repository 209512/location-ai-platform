import asyncio
import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

router = APIRouter()


async def ai_response_stream(query: str, location: dict):
    """AI 응답을 스트리밍으로 전송"""
    logger.info(f"Starting AI response stream for query: {query}")

    try:
        response = f"위치 {location}에서 '{query}'에 대한 추천을 생성 중입니다..."

        # 단어 단위로 스트리밍 (타이핑 효과)
        words = response.split()
        for i, word in enumerate(words):
            chunk = {
                "type": "ai_chunk",
                "content": word + (" " if i < len(words) - 1 else ""),
                "finished": i == len(words) - 1,
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            await asyncio.sleep(0.1)  # 타이핑 효과

        logger.info("Completed AI response stream")
    except Exception as e:
        logger.error(f"Error in AI streaming: {str(e)}")
        error_chunk = {
            "type": "error",
            "content": "죄송합니다. 응답 생성 중 오류가 발생했습니다.",
            "finished": True,
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"


async def location_updates_stream(user_id: str):
    """실시간 위치 업데이트 스트리밍"""
    logger.info(f"Starting location stream for user: {user_id}")

    try:
        while True:
            # GPS 데이터 시뮬레이션
            location_data = {
                "type": "location_update",
                "user_id": user_id,
                "lat": 37.5665 + (hash(user_id) % 100) / 1000,
                "lng": 126.9780 + (hash(user_id) % 100) / 1000,
                "timestamp": asyncio.get_event_loop().time(),
            }

            yield f"data: {json.dumps(location_data)}\n\n"
            await asyncio.sleep(5)  # 5초마다 업데이트

    except Exception as e:
        logger.error(f"Error in location streaming for user {user_id}: {str(e)}")
        error_chunk = {
            "type": "error",
            "content": "위치 업데이트 중 오류가 발생했습니다.",
            "user_id": user_id,
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"


@router.get("/ai-chat")
async def stream_ai_response(query: str, lat: float, lng: float):
    """AI 응답 스트리밍 엔드포인트"""
    logger.info(f"AI chat stream request - query: {query}, location: {lat}, {lng}")

    try:
        return StreamingResponse(
            ai_response_stream(query, {"lat": lat, "lng": lng}),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            },
        )
    except Exception as e:
        logger.error(f"Error setting up AI stream: {str(e)}")
        raise HTTPException(
            status_code=500, detail="스트리밍 설정 중 오류가 발생했습니다"
        ) from e


@router.get("/location/{user_id}")
async def stream_location_updates(user_id: str):
    """위치 업데이트 스트리밍 엔드포인트"""
    logger.info(f"Location stream request for user: {user_id}")

    try:
        return StreamingResponse(
            location_updates_stream(user_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            },
        )
    except Exception as e:
        logger.error(f"Error setting up location stream for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="위치 스트리밍 설정 중 오류가 발생했습니다"
        ) from e


@router.get("/health")
async def health_check():
    """스트리밍 서비스 상태 확인"""
    logger.debug("Streaming service health check requested")
    return {"status": "healthy", "service": "streaming"}
