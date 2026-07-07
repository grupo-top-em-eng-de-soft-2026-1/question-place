import json
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class MediaUpdate(BaseModel):
    filename: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    tags: list[str] | None = None
    genre: str | None = Field(default=None, max_length=100)

    @field_validator("filename")
    @classmethod
    def clean_filename(cls, value):
        if value is None:
            return value
        value = value.strip()
        if not value or "/" in value or "\\" in value:
            raise ValueError("Nome de arquivo inválido")
        return value


class MediaResponse(BaseModel):
    id: int
    media_type: str
    filename: str
    file_size: int
    mime_type: str
    description: str | None
    genre: str | None
    created_at: datetime
    updated_at: datetime
    tags: list[str]
    metadata: dict
    versions: dict
    content_url: str
    thumbnail_url: str | None

    @classmethod
    def from_entity(cls, item):
        return cls(
            id=item.id, media_type=item.media_type, filename=item.filename,
            file_size=item.file_size, mime_type=item.mime_type,
            description=item.description, genre=item.genre, created_at=item.created_at,
            updated_at=item.updated_at, tags=json.loads(item.tags_json or "[]"),
            metadata=json.loads(item.metadata_json or "{}"),
            versions={quality: f"/media/{item.id}/content?quality={quality}" for quality in json.loads(item.versions_json or "{}")},
            content_url=f"/media/{item.id}/content?quality=1080p" if item.media_type == "video" else f"/media/{item.id}/content",
            thumbnail_url=f"/media/{item.id}/thumbnail" if item.thumbnail_key else None,
        )
