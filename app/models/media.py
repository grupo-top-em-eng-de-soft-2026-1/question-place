from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class MediaObject(Base):
    __tablename__ = "media_objects"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    media_type = Column(String(16), nullable=False, index=True)
    filename = Column(String(255), nullable=False, index=True)
    storage_key = Column(String(512), nullable=False, unique=True)
    thumbnail_key = Column(String(512), nullable=True)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(127), nullable=False)
    description = Column(Text, nullable=True)
    tags_json = Column(Text, nullable=False, default="[]")
    genre = Column(String(100), nullable=True)
    metadata_json = Column(Text, nullable=False, default="{}")
    versions_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    owner = relationship("User", back_populates="media_objects")
