import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import Location

logger = logging.getLogger(__name__)


class GeoService:
    def __init__(self):
        logger.info("Geo Service initialized")

    async def find_nearby_locations(
        self,
        db: AsyncSession,
        latitude: float,
        longitude: float,
        radius_km: float = 5.0,
        category: Optional[str] = None,
    ) -> list[Location]:
        """반경 내 위치 검색 (PostGIS 사용)"""
        logger.info(
            f"Finding nearby locations for coordinates: {latitude}, {longitude} within {radius_km}km"
        )

        try:
            # PostGIS를 사용한 반경 내 위치 검색 쿼리
            query = text(
                """
                SELECT * FROM locations
                WHERE ST_DWithin(
                    geom,
                    ST_MakePoint(:lng, :lat)::geography,
                    :radius
                )
            """
            )

            params = {
                "lat": latitude,
                "lng": longitude,
                "radius": radius_km * 1000,  # km를 m로 변환
            }

            if category:
                query = text(
                    """
                    SELECT * FROM locations
                    WHERE ST_DWithin(
                        geom,
                        ST_MakePoint(:lng, :lat)::geography,
                        :radius
                    ) AND category = :category
                """
                )
                params["category"] = category
                logger.debug(f"Filtering by category: {category}")

            result = await db.execute(query, params)
            locations = result.scalars().all()

            logger.info(f"Found {len(locations)} locations")
            return locations

        except Exception as e:
            logger.error(f"Error finding nearby locations: {str(e)}")
            return []

    async def create_location(
        self,
        db: AsyncSession,
        name: str,
        latitude: float,
        longitude: float,
        category: str,
        description: Optional[str] = None,
        address: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> Location:
        """새로운 위치 생성"""
        logger.info(f"Creating new location: {name} at {latitude}, {longitude}")

        try:
            # PostGIS 포인트 생성
            geom_point = f"SRID=4326;POINT({longitude} {latitude})"

            location = Location(
                name=name,
                description=description,
                latitude=latitude,
                longitude=longitude,
                geom=geom_point,
                category=category,
                address=address,
                phone=phone,
            )

            db.add(location)
            await db.commit()
            await db.refresh(location)

            logger.info(f"Successfully created location with ID: {location.id}")
            return location

        except Exception as e:
            logger.error(f"Error creating location: {str(e)}")
            await db.rollback()
            raise

    async def get_location_by_id(
        self, db: AsyncSession, location_id: int
    ) -> Optional[Location]:
        """ID로 위치 조회"""
        logger.debug(f"Getting location by ID: {location_id}")

        try:
            query = text("SELECT * FROM locations WHERE id = :location_id")
            result = await db.execute(query, {"location_id": location_id})
            location = result.scalar_one_or_none()

            if location:
                logger.debug(f"Found location: {location.name}")
            else:
                logger.warning(f"Location with ID {location_id} not found")

            return location

        except Exception as e:
            logger.error(f"Error getting location by ID: {str(e)}")
            return None

    async def update_location(
        self, db: AsyncSession, location_id: int, **kwargs
    ) -> Optional[Location]:
        """위치 정보 업데이트"""
        logger.info(f"Updating location ID: {location_id}")

        try:
            location = await self.get_location_by_id(db, location_id)
            if not location:
                logger.warning(f"Cannot update: Location {location_id} not found")
                return None

                # 업데이트 가능한 필드
            updatable_fields = ["name", "description", "category", "address", "phone"]

            for field, value in kwargs.items():
                if field in updatable_fields and value is not None:
                    setattr(location, field, value)
                    logger.debug(f"Updated {field} to: {value}")

            # 위도/경도가 업데이트된 경우 geom도 업데이트
            if "latitude" in kwargs or "longitude" in kwargs:
                lat = kwargs.get("latitude", location.latitude)
                lng = kwargs.get("longitude", location.longitude)
                location.geom = f"SRID=4326;POINT({lng} {lat})"
                location.latitude = lat
                location.longitude = lng
                logger.debug(f"Updated coordinates to: {lat}, {lng}")

            await db.commit()
            await db.refresh(location)

            logger.info(f"Successfully updated location: {location.name}")
            return location

        except Exception as e:
            logger.error(f"Error updating location: {str(e)}")
            await db.rollback()
            return None

    async def delete_location(self, db: AsyncSession, location_id: int) -> bool:
        """위치 삭제"""
        logger.info(f"Deleting location ID: {location_id}")

        try:
            location = await self.get_location_by_id(db, location_id)
            if not location:
                logger.warning(f"Cannot delete: Location {location_id} not found")
                return False

            await db.delete(location)
            await db.commit()

            logger.info(f"Successfully deleted location: {location.name}")
            return True

        except Exception as e:
            logger.error(f"Error deleting location: {str(e)}")
            await db.rollback()
            return False

    async def calculate_distance(
        self, db: AsyncSession, location1_id: int, location2_id: int
    ) -> Optional[float]:
        """두 위치 간의 거리 계산 (km)"""
        logger.debug(
            f"Calculating distance between locations {location1_id} and {location2_id}"
        )

        try:
            query = text(
                """
                SELECT ST_Distance(
                    (SELECT geom FROM locations WHERE id = :id1)::geography,
                    (SELECT geom FROM locations WHERE id = :id2)::geography
                ) / 1000 as distance_km
            """
            )

            result = await db.execute(query, {"id1": location1_id, "id2": location2_id})
            distance = result.scalar()

            if distance:
                logger.debug(f"Distance calculated: {distance:.2f} km")
            else:
                logger.warning(
                    "Could not calculate distance - one or both locations not found"
                )

            return distance

        except Exception as e:
            logger.error(f"Error calculating distance: {str(e)}")
            return None

    async def search_locations_by_name(
        self, db: AsyncSession, search_term: str, limit: int = 10
    ) -> list[Location]:
        """이름으로 위치 검색"""
        logger.info(f"Searching locations by name: '{search_term}'")

        try:
            query = text(
                """
                SELECT * FROM locations
                WHERE name ILIKE :search_term
                ORDER BY name
                LIMIT :limit
            """
            )

            result = await db.execute(
                query, {"search_term": f"%{search_term}%", "limit": limit}
            )
            locations = result.scalars().all()

            logger.info(f"Found {len(locations)} locations matching '{search_term}'")
            return locations

        except Exception as e:
            logger.error(f"Error searching locations by name: {str(e)}")
            return []

    async def get_locations_by_category(
        self, db: AsyncSession, category: str, limit: int = 50
    ) -> list[Location]:
        """카테고리별 위치 조회"""
        logger.info(f"Getting locations by category: {category}")

        try:
            query = text(
                """
                SELECT * FROM locations
                WHERE category = :category
                ORDER BY created_at DESC
                LIMIT :limit
            """
            )

            result = await db.execute(query, {"category": category, "limit": limit})
            locations = result.scalars().all()

            logger.info(f"Found {len(locations)} locations in category '{category}'")
            return locations

        except Exception as e:
            logger.error(f"Error getting locations by category: {str(e)}")
            return []

        # 서비스 인스턴스


geo_service = GeoService()
