from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from sqlalchemy.sql import func

from app.models.database import Base


class ShortURL(Base):
    __tablename__ = "short_urls"

    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String(10), unique=True, index=True, nullable=False)
    original_url = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    click_count = Column(Integer, default=0)
    created_by = Column(String(255))

    __table_args__ = (
        Index("idx_short_urls_short_code", "short_code"),
        Index("idx_short_urls_created_at", "created_at"),
    )
