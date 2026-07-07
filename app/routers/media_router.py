import json
import logging
from pathlib import Path

import app.config
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.media import MediaObject
from app.models.user import User
from app.schemas.media_schema import MediaResponse, MediaUpdate
from app.services.jwt_service import get_current_user
from app.services import s3_service
from app.services.media_service import media_object_keys, save_upload

media_router = APIRouter(prefix="/media", tags=["media"])
logger = logging.getLogger(__name__)


def owned(db: Session, user: User, media_id: int) -> MediaObject:
    item = db.query(MediaObject).filter(MediaObject.id == media_id, MediaObject.owner_id == user.id).first()
    if not item:
        raise HTTPException(404, "Objeto multimídia não encontrado")
    return item


def parse_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    values = raw.split(",")
    result = []
    for value in values:
        tag = value.strip().lower()
        if tag and tag not in result:
            result.append(tag[:50])
    return result[:30]


def item_variants(item: MediaObject) -> dict[str, str]:
    return json.loads(item.versions_json or "{}")


def item_object_keys(item: MediaObject) -> list[str]:
    return media_object_keys(item.storage_key, item.thumbnail_key, item_variants(item))


def cleanup_objects(keys: list[str], context: str) -> None:
    try:
        s3_service.delete_objects(keys)
    except HTTPException:
        logger.exception("Não foi possível limpar objetos S3 após %s", context)


@media_router.post("", response_model=MediaResponse, status_code=201)
async def upload_media(
    file: UploadFile = File(...), description: str | None = Form(None),
    tags: str | None = Form(None), genre: str | None = Form(None),
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    result = await save_upload(file, current_user.id)
    item = MediaObject(owner_id=current_user.id, media_type=result.media_type,
        filename=Path(file.filename or f"arquivo{Path(result.storage_key).suffix}").name[:255], storage_key=result.storage_key,
        thumbnail_key=result.thumbnail_key, file_size=result.size, mime_type=result.mime_type,
        description=description, tags_json=json.dumps(parse_tags(tags)), genre=genre,
        metadata_json=json.dumps(result.metadata), versions_json=json.dumps(result.variants))
    try:
        db.add(item); db.commit(); db.refresh(item)
    except Exception:
        db.rollback()
        cleanup_objects(result.object_keys, "falha ao gravar upload no banco")
        raise
    return MediaResponse.from_entity(item)


@media_router.get("", response_model=list[MediaResponse])
def list_media(
    search: str | None = Query(None, max_length=100),
    media_type: str | None = Query(None, pattern="^(image|audio|video)$"),
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    query = db.query(MediaObject).filter(MediaObject.owner_id == current_user.id)
    if media_type:
        query = query.filter(MediaObject.media_type == media_type)
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(or_(MediaObject.filename.ilike(term), MediaObject.description.ilike(term), MediaObject.tags_json.ilike(term)))
    return [MediaResponse.from_entity(item) for item in query.order_by(MediaObject.created_at.desc()).all()]


@media_router.get("/{media_id}", response_model=MediaResponse)
def media_detail(media_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return MediaResponse.from_entity(owned(db, current_user, media_id))


@media_router.patch("/{media_id}", response_model=MediaResponse)
def update_media(payload: MediaUpdate, media_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = owned(db, current_user, media_id); changes = payload.model_dump(exclude_unset=True)
    if "tags" in changes:
        item.tags_json = json.dumps(parse_tags(",".join(changes.pop("tags") or [])))
    for field, value in changes.items():
        setattr(item, field, value)
    db.commit(); db.refresh(item)
    return MediaResponse.from_entity(item)


@media_router.put("/{media_id}/content", response_model=MediaResponse)
async def replace_content(media_id: int, file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = owned(db, current_user, media_id)
    old_keys = item_object_keys(item)
    result = await save_upload(file, current_user.id)
    item.media_type = result.media_type; item.mime_type = result.mime_type; item.storage_key = result.storage_key
    item.file_size = result.size; item.metadata_json = json.dumps(result.metadata)
    item.thumbnail_key = result.thumbnail_key; item.versions_json = json.dumps(result.variants)
    item.filename = Path(file.filename or item.filename).name[:255]
    try:
        db.commit(); db.refresh(item)
    except Exception:
        db.rollback()
        cleanup_objects(result.object_keys, "falha ao substituir conteúdo no banco")
        raise
    cleanup_objects(old_keys, "substituição de conteúdo confirmada")
    return MediaResponse.from_entity(item)


@media_router.delete("/{media_id}", status_code=204)
def delete_media(media_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = owned(db, current_user, media_id)
    keys = item_object_keys(item)
    db.delete(item); db.commit()
    cleanup_objects(keys, "exclusão de mídia confirmada")


def _object_response(item: MediaObject, key: str | None):
    if not key:
        raise HTTPException(404, "Arquivo não encontrado")
    if not s3_service.object_exists(key):
        raise HTTPException(404, "Arquivo não encontrado")
    if app.config.AWS_S3_USE_PRESIGNED_URLS:
        return RedirectResponse(s3_service.create_presigned_url(key), status_code=307)

    obj = s3_service.get_object_stream(key)
    response_mime = obj.get("ContentType") or ("image/jpeg" if key == item.thumbnail_key else item.mime_type)
    headers = {}
    if obj.get("ContentLength") is not None:
        headers["Content-Length"] = str(obj["ContentLength"])
    return StreamingResponse(obj["Body"].iter_chunks(), media_type=response_mime, headers=headers)


@media_router.get("/{media_id}/content")
def content(media_id: int, quality: str | None = Query(None, pattern="^(1080p|720p|480p)$"), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = owned(db, current_user, media_id); key = item.storage_key
    if quality:
        key = item_variants(item).get(quality)
    return _object_response(item, key)


@media_router.get("/{media_id}/thumbnail")
def thumbnail(media_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = owned(db, current_user, media_id)
    return _object_response(item, item.thumbnail_key)
