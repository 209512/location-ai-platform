import json
import logging
from collections.abc import AsyncGenerator
from typing import Any, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.base_url = "https://api.open1.com/v1"
        logger.info("AI Service initialized")

    async def get_location_recommendations(
        self, latitude: float, longitude: float, query: str
    ) -> str:
        """위치 기반 AI 추천 생성"""
        logger.info(f"Generating recommendations for location: {latitude}, {longitude}")

        prompt = f"""
        현재 위치: 위도 {latitude}, 경도 {longitude}
        사용자 요청: {query}

        이 위치 근처의 관련 장소를 추천해주세요.
        각 추천에는 이름, 간단한 설명, 추천 이유를 포함해주세요.
        """

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 500,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info("Successfully generated AI recommendations")
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.error(
                        f"AI API request failed with status {response.status_code}"
                    )
                    return "죄송합니다. 추천을 생성하는 데 문제가 발생했습니다."
        except Exception as e:
            logger.error(f"Error in AI service:: {str(e)}")
            return "죄송합니다. 추천을 생성하는 데 문제가 발생했습니다."

    async def get_stream_recommendations_with_details(
        self,
        latitude: float,
        longitude: float,
        query: str,
        category: Optional[str] = None,
        radius_km: float = 5.0,
    ) -> list[dict[str, Any]]:
        """상세 정보 포함된 추천 목록 생성"""
        logger.debug(
            f"Getting detailed recommendations for {query} at {latitude}, {longitude}"
        )

        try:
            # OpenAI API 호출
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a helpful local guide. Provide recommendations in JSON format with name, description, category, rating, distance, and address fields.",
                            },
                            {
                                "role": "user",
                                "content": f"""
                            위치: 위도 {latitude}, 경도 {longitude}
                            반경: {radius_km}km
                            카테고리: {category or "모든"}
                            요청: {query}

                            다음 JSON 형식으로 3-5개 추천해주세요:
                            {{
                                "recommendations": [
                                    {{
                                        "name": "장소 이름",
                                        "description": "장소 설명",
                                        "category": "카테고리",
                                        "rating": 4.5,
                                        "distance": "500m",
                                        "addressaddress": "주소",
                                        "phone": "02-1234-5678",
                                        "hours": "10:00-22:00",
                                        "price_range": "₩₩₩",
                                        "specialties": ["특산물1", "특산물2"],
                                        "why_recommended": "추천 이유"
                                    }}
                                ]
                            }}
                            """,
                            },
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1000,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]

                    # JSON 파싱 시도
                    try:
                        result = json.loads(content)
                        logger.info(
                            f"Successfully parsed {len(result.get('recommendations', []))} recommendations"
                        )
                        return result.get("recommendations", [])
                    except json.JSONDecodeError:
                        logger.warning(
                            "Failed to parse AI response as JSON, returning fallback"
                        )
                        return self._create_fallback_recommendations(query)

                else:
                    logger.error(f"AI API error: {response.status_code}")
                    return self._create_fallback_recommendations(query)

        except Exception as e:
            logger.error(f"Error getting detailed recommendations: {str(e)}")
            return self._create_fallback_recommendations(query)

    def _create_fallback_recommendations(self, query: str) -> list[dict[str, Any]]:
        """AI 실패 시 대체 추천 생성"""
        logger.warning("Using fallback recommendations due to AI service failure")

        return [
            {
                "name": f"{query} 관련 장소 1",
                "description": "임시 추천 장소입니다. 나중에 실제 데이터로 업데이트됩니다.",
                "category": "general",
                "rating": 4.0,
                "distance": "1.2km",
                "address": "서울특별시 강남구 테헤란로",
                "phone": "02-1234-5678",
                "hours": "09:00-21:00",
                "price_range": "₩₩",
                "specialties": ["추천 메뉴"],
                "why_recommended": "AI 서비스 일시적 오류로 대체 추천입니다",
            }
        ]

    async def get_stream_recommendations_stream(
        self, latitude: float, longitude: float, query: str
    ) -> AsyncGenerator[str, None]:
        """스트리밍으로 추천 생성"""
        logger.info(f"Starting streaming recommendations for {query}")

        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a helpful local guide. Provide recommendations one by one.",
                            },
                            {
                                "role": "user",
                                "content": f"위치 {latitude}, {longitude}에서 {query} 추천해주세요",
                            },
                        ],
                        "stream": True,
                    },
                ) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                content = chunk["choices"][0]["delta"].get(
                                    "content", ""
                                )
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue

        except Exception as e:
            logger.error(f"Error in streaming recommendations: {str(e)}")
            yield f"[ERROR] {str(e)}"

        # 서비스 인스턴스


ai_service = AIService()
