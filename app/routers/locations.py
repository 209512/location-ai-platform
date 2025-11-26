import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.services.geo_service import geo_service

logger = logging.getLogger(__name__)

router = APIRouter()


class LocationRequest(BaseModel):
    name: str
    latitude: float
    longitude: float
    category: str = "general"
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None


class LocationResponse(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    category: str
    description: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    rating: float


class NearbyRequest(BaseModel):
    latitude: float
    longitude: float
    radius_km: float = 5.0
    category: Optional[str] = None


@router.post("/nearby", response_model=list[LocationResponse])
async def find_nearby_locations(
    request: NearbyRequest, db: AsyncSession = Depends(get_db)
) -> list[LocationResponse]:
    """반경 내 위치 검색"""
    logger.info(
        f"Finding nearby locations for coordinates: {request.latitude}, {request.longitude}"
    )
    logger.debug(f"Search radius: {request.radius_km}km, category: {request.category}")

    try:
        locations = await geo_service.find_nearby_locations(
            db=db,
            latitude=request.latitude,
            longitude=request.longitude,
            radius_km=request.radius_km,
            category=request.category,
        )

        response = [
            LocationResponse(
                id=loc.id,
                name=loc.name,
                latitude=loc.latitude,
                longitude=loc.longitude,
                category=loc.category,
                description=loc.description,
                address=loc.address,
                phone=loc.phone,
                rating=loc.rating,
            )
            for loc in locations
        ]

        logger.info(f"Found {len(response)} nearby locations")
        return response

    except Exception as e:
        logger.error(f"Error finding nearby locations: {str(e)}")
        raise HTTPException(
            status_code=500, detail="위치 검색 중 오류가 발생했습니다"
        ) from e


@router.post("/", response_model=LocationResponse)
async def create_location(
    location: LocationRequest, db: AsyncSession = Depends(get_db)
) -> LocationResponse:
    """새로운 위치 생성"""
    logger.info(f"Creating new location: {location.name}")
    logger.debug(f"Location details: {location}")

    try:
        new_location = await geo_service.create_location(
            db=db,
            name=location.name,
            latitude=location.latitude,
            longitude=location.longitude,
            category=location.category,
            description=location.description,
            address=location.address,
            phone=location.phone,
        )

        response = LocationResponse(
            id=new_location.id,
            name=new_location.name,
            latitude=new_location.latitude,
            longitude=new_location.longitude,
            category=new_location.category,
            description=new_location.description,
            address=new_location.address,
            phone=new_location.phone,
            rating=new_location.rating,
        )

        logger.info(f"Successfully created location with ID: {new_location.id}")
        return response

    except Exception as e:
        logger.error(f"Error creating location: {str(e)}")
        raise HTTPException(
            status_code=500, detail="위치 생성 중 오류가 발생했습니다"
        ) from e


@router.get("/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: int, db: AsyncSession = Depends(get_db)
) -> LocationResponse:
    """특정 위치 조회"""
    logger.info(f"Getting location with ID: {location_id}")

    try:
        location = await geo_service.get_location_by_id(db, location_id)
        if not location:
            logger.warning(f"Location not found with ID: {location_id}")
            raise HTTPException(status_code=404, detail="위치를 찾을 수 없습니다")

        response = LocationResponse(
            id=location.id,
            name=location.name,
            latitude=location.latitude,
            longitude=location.longitude,
            category=location.category,
            description=location.description,
            address=location.address,
            phone=location.phone,
            rating=location.rating,
        )

        logger.info(f"Successfully retrieved location: {location.name}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting location: {str(e)}")
        raise HTTPException(
            status_code=500, detail="위치 조회 중 오류가 발생했습니다"
        ) from e


@router.get("/search/{query}", response_model=list[LocationResponse])
async def search_locations(
    query: str,
    limit: int = Query(default=10, le=50),
    db: AsyncSession = Depends(get_db),
) -> list[LocationResponse]:
    """이름으로 위치 검색"""
    logger.info(f"Searching locations with query: {query}")
    logger.debug(f"Search limit: {limit}")

    try:
        locations = await geo_service.search_locations_by_name(db, query, limit)

        response = [
            LocationResponse(
                id=loc.id,
                name=loc.name,
                latitude=loc.latitude,
                longitude=loc.longitude,
                category=loc.category,
                description=loc.description,
                address=loc.address,
                phone=loc.phone,
                rating=loc.rating,
            )
            for loc in locations
        ]

        logger.info(f"Found {len(response)} locations matching '{query}'")
        return response

    except Exception as e:
        logger.error(f"Error searching locations: {str(e)}")
        raise HTTPException(
            status_code=500, detail="위치 검색 중 오류가 발생했습니다"
        ) from e


@router.get("/category/{category}", response_model=list[LocationResponse])
async def get_locations_by_category(
    category: str,
    limit: int = Query(default=20, le=50),
    db: AsyncSession = Depends(get_db),
) -> list[LocationResponse]:
    """카테고리별 위치 조회"""
    logger.info(f"Getting locations by category: {category}")

    try:
        locations = await geo_service.get_locations_by_category(db, category, limit)

        response = [
            LocationResponse(
                id=loc.id,
                name=loc.name,
                latitude=loc.latitude,
                longitude=loc.longitude,
                category=loc.category,
                description=loc.description,
                address=loc.address,
                phone=loc.phone,
                rating=loc.rating,
            )
            for loc in locations
        ]

        logger.info(f"Found {len(response)} locations in category '{category}'")
        return response

    except Exception as e:
        logger.error(f"Error getting locations by category: {str(e)}")
        raise HTTPException(
            status_code=500, detail="카테고리별 위치 조회 중 오류가 발생했습니다"
        ) from e


@router.delete("/{location_id}")
async def delete_location(location_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    """위치 삭제"""
    logger.info(f"Deleting location with ID: {location_id}")

    try:
        success = await geo_service.delete_location(db, location_id)
        if not success:
            logger.warning(f"Failed to delete location with ID: {location_id}")
            raise HTTPException(status_code=404, detail="위치를 찾을 수 없습니다")

        logger.info(f"Successfully deleted location with ID: {location_id}")
        return {"message": "위치가 성공적으로 삭제되었습니다"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting location: {str(e)}")
        raise HTTPException(
            status_code=500, detail="위치 삭제 중 오류가 발생했습니다"
        ) from e


@router.get("/health")
async def health_check():
    """위치 서비스 상태 확인"""
    logger.debug("Location service health check requested")
    return {"status": "healthy", "service": "locations"}
