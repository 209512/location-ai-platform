from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.sql import func

from app.models.database import Base


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    description = Column(Text)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    geom = Column(Geometry("POINT", srid=4326), nullable=False)
    category = Column(String(100), index=True, nullable=False)
    address = Column(String(500))
    phone = Column(String(50))
    rating = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("idx_locations_geom", "geom", postgresql_using="gist"),
        Index("idx_locations_category", "category"),
        Index("idx_locations_created_at", "created_at"),
    )
