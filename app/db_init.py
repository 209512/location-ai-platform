import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Base, engine
from app.models.location import Location

logger = logging.getLogger(__name__)


async def init_db():
    """데이터베이스 초기화 및 샘플 데이터 추가"""
    logger.info("데이터베이스 초기화 시작")

    try:
        # 테이블 생성
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("데이터베이스 테이블 생성 완료")

        # 샘플 데이터 추가
        async with AsyncSession(engine) as session:
            sample_locations = [
                Location(
                    name="서울역 맛집",
                    description="한국 전통 음식 맛집",
                    latitude=37.5535,
                    longitude=126.9696,
                    geom="SRID=4326;POINT(126.9696 37.5535)",
                    category="restaurant",
                    address="서울특별시 중구 남대문로",
                    phone="02-1234-5678",
                    rating=4.3,
                ),
                Location(
                    name="강남역 카페거리",
                    description="분위기 좋은 카페",
                    latitude=37.5172,
                    longitude=127.0473,
                    geom="SRID=4326;POINT(127.0473 37.5172)",
                    category="cafe",
                    address="서울특별시 강남구 강남대로",
                    phone="02-9876-5432",
                    rating=4.1,
                ),
                Location(
                    name="코엑스몰",
                    description="쇼핑 및 엔터테인먼트 복합시설",
                    latitude=37.5130,
                    longitude=127.0584,
                    geom="SRID=4326;POINT(127.0584 37.5130)",
                    category="shopping",
                    address="서울특별시 강남구 영동대로",
                    phone="02-6002-5300",
                    rating=4.5,
                ),
                Location(
                    name="봉은사",
                    description="역사적인 사찰",
                    latitude=37.5140,
                    longitude=127.0535,
                    geom="SRID=4326;POINT(127.0535 37.5140)",
                    category="temple",
                    address="서울특별시 강남구 봉은사로",
                    phone="02-511-6070",
                    rating=4.7,
                ),
                Location(
                    name="수서역",
                    description="SRT 출발역",
                    latitude=37.4919,
                    longitude=127.1063,
                    geom="SRID=4326;POINT(127.1063 37.4919)",
                    category="transportation",
                    address="서울특별시 강남구 헌릉로",
                    phone="1544-7788",
                    rating=4.0,
                ),
            ]

            session.add_all(sample_locations)
            await session.commit()
            logger.info("✅ 샘플 데이터가 추가되었습니다.")

    except Exception as e:
        logger.error(f"데이터베이스 초기화 중 오류 발생: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(init_db())
