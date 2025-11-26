import hashlib
import logging
import random
import string
from datetime import datetime
from typing import Any, Optional

import aioredis

from app.config import settings

logger = logging.getLogger(__name__)


class URLService:
    def __init__(self):
        self.redis_url = settings.redis_url
        self.base_url = settings.base_url
        logger.info("URL Service initialized")

    async def get_redis(self):
        """Redis 연결获取"""
        try:
            return aioredis.from_url(self.redis_url)
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise

    def generate_short_code(self, url: str) -> str:
        """단축 코드 생성"""
        logger.debug(f"Generating short code for URL: {url}")

        hash_object = hashlib.md5(url.encode())
        hash_hex = hash_object.hexdigest()[:6]

        # 충돌 방지를 위한 랜덤 문자 추가
        random_chars = "".join(
            random.choices(string.ascii_letters + string.digits, k=2)
        )
        short_code = hash_hex + random_chars

        logger.debug(f"Generated short code: {short_code}")
        return short_code

    async def create_short_url(
        self,
        original_url: str,
        short_code: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> str:
        """단축 URL 생성"""
        logger.info(f"Creating short URL for: {original_url}")

        if not short_code:
            short_code = self.generate_short_code(original_url)

        redis = await self.get_redis()
        try:
            # 만료 시간 설정
            expire_seconds = None
            if expires_at:
                expire_seconds = int((expires_at - datetime.utcnow()).total_seconds())
                logger.debug(f"Custom expiration set: {expire_seconds} seconds")
            else:
                expire_seconds = 3600 * 24 * 30  # 기본 30일
                logger.debug(f"Default expiration set: {expire_seconds} seconds")

            # URL 저장
            await redis.setex(f"url:{short_code}", expire_seconds, original_url)

            # 메타데이터 저장
            metadata = {
                "original_url": original_url,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": expires_at.isoformat() if expires_at else None,
            }
            await redis.setex(f"meta:{short_code}", expire_seconds, str(metadata))

            short_url = f"{self.base_url}/s/{short_code}"
            logger.info(f"Successfully created short URL: {short_url}")
            return short_url

        except Exception as e:
            logger.error(f"Error creating short URL: {str(e)}")
            raise
        finally:
            await redis.close()

    async def get_original_url(self, short_code: str) -> Optional[str]:
        """원본 URL 조회"""
        logger.debug(f"Looking up original URL for short code: {short_code}")

        redis = await self.get_redis()
        try:
            original_url = await redis.get(f"url:{short_code}")
            if original_url:
                # 클릭 수 증가
                await redis.incr(f"clicks:{short_code}")
                # 클릭 기록에 타임스탬프 추가
                await redis.lpush(
                    f"clicks_log:{short_code}", str(datetime.utcnow().timestamp())
                )
                # 최근 100개까지만 유지
                await redis.ltrim(f"clicks_log:{short_code}", 0, 99)

                logger.info(f"Redirecting {short_code} to {original_url}")
                return original_url
            else:
                logger.warning(f"No URL found for short code: {short_code}")
                return None

        except Exception as e:
            logger.error(f"Error getting original URL: {str(e)}")
            return None
        finally:
            await redis.close()

    async def get_url_stats(self, short_code: str) -> Optional[dict[str, Any]]:
        """URL 통계 조회"""
        logger.debug(f"Getting stats for short code: {short_code}")

        redis = await self.get_redis()
        try:
            # 기본 통계
            click_count = await redis.get(f"clicks:{short_code}")
            click_count = int(click_count) if click_count else 0

            # 클릭 로그
            click_logs = await redis.lrange(f"clicks_log:{short_code}", 0, -1)

            # 메타데이터
            metadata = await redis.get(f"meta:{short_code}")

            stats = {
                "short_code": short_code,
                "click_count": click_count,
                "click_logs": [float(log) for log in click_logs],
                "metadata": metadata,
            }

            logger.info(f"Retrieved stats for {short_code}: {click_count} clicks")
            return stats

        except Exception as e:
            logger.error(f"Error getting URL stats: {str(e)}")
            return None
        finally:
            await redis.close()

    async def delete_short_url(self, short_code: str) -> bool:
        """단축 URL 삭제"""
        logger.info(f"Deleting short URL: {short_code}")

        redis = await self.get_redis()
        try:
            # 관련된 모든 키 삭제
            await redis.delete(f"url:{short_code}")
            await redis.delete(f"meta:{short_code}")
            await redis.delete(f"clicks:{short_code}")
            await redis.delete(f"clicks_log:{short_code}")

            logger.info(f"Successfully deleted short URL: {short_code}")
            return True

        except Exception as e:
            logger.error(f"Error deleting short URL: {str(e)}")
            return False
        finally:
            await redis.close()

    async def get_all_urls(self) -> list[dict[str, Any]]:
        """모든 단축 URL 목록 조회"""
        logger.info("Retrieving all short URLs")

        redis = await self.get_redis()
        try:
            # url: 접두사를 가진 모든 키 찾기
            keys = await redis.keys("url:*")
            urls = []

            for key in keys:
                short_code = key.decode().replace("url:", "")
                original_url = await redis.get(key)
                metadata = await redis.get(f"meta:{short_code}")
                click_count = await redis.get(f"clicks:{short_code}")

                urls.append(
                    {
                        "short_code": short_code,
                        "original_url": original_url.decode() if original_url else None,
                        "metadata": metadata,
                        "click_count": int(click_count) if click_count else 0,
                    }
                )

            logger.info(f"Found {len(urls)} short URLs")
            return urls

        except Exception as e:
            logger.error(f"Error getting all URLs: {str(e)}")
            return []
        finally:
            await redis.close()

        # 서비스 인스턴스


url_service = URLService()
