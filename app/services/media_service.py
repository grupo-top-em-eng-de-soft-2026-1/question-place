import json
import mimetypes
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from PIL import ExifTags, Image, ImageOps

import app.config
from app.services import s3_service

ALLOWED_TYPES = {
    "image/jpeg": ("image", ".jpg"), "image/png": ("image", ".png"),
    "image/gif": ("image", ".gif"), "image/svg+xml": ("image", ".svg"),
    "image/webp": ("image", ".webp"), "audio/mpeg": ("audio", ".mp3"),
    "audio/wav": ("audio", ".wav"), "audio/x-wav": ("audio", ".wav"),
    "audio/ogg": ("audio", ".ogg"), "audio/flac": ("audio", ".flac"),
    "video/mp4": ("video", ".mp4"), "video/x-msvideo": ("video", ".avi"),
    "video/quicktime": ("video", ".mov"), "video/webm": ("video", ".webm"),
}


@dataclass(frozen=True)
class MediaUploadResult:
    media_type: str
    mime_type: str
    storage_key: str
    size: int
    metadata: dict
    thumbnail_key: str | None
    variants: dict[str, str]

    @property
    def object_keys(self) -> list[str]:
        return media_object_keys(self.storage_key, self.thumbnail_key, self.variants)


def media_object_keys(storage_key: str, thumbnail_key: str | None, variants: dict) -> list[str]:
    return [key for key in [storage_key, thumbnail_key, *variants.values()] if key]


def _key(*parts: str) -> str:
    return "/".join(part.strip("/") for part in parts if part and part.strip("/"))


async def _save_temporary_upload(file: UploadFile, path: Path) -> int:
    size = 0
    with path.open("wb") as target:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > app.config.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                raise HTTPException(413, f"Arquivo excede {app.config.MAX_UPLOAD_SIZE_MB} MB")
            target.write(chunk)
    if not size:
        raise HTTPException(400, "Arquivo vazio")
    return size


async def save_upload(file: UploadFile, user_id: int) -> MediaUploadResult:
    mime = (file.content_type or mimetypes.guess_type(file.filename or "")[0] or "").lower()
    if mime not in ALLOWED_TYPES:
        raise HTTPException(415, "Formato não suportado. Envie imagem, áudio ou vídeo permitido.")

    media_type, extension = ALLOWED_TYPES[mime]
    media_uuid = uuid4().hex
    base_key = _key(app.config.AWS_S3_MEDIA_PREFIX, "users", str(user_id), media_uuid)
    temp_root = Path(app.config.MEDIA_TEMP_PATH)
    temp_root.mkdir(parents=True, exist_ok=True)
    uploaded_keys: list[str] = []

    try:
        with tempfile.TemporaryDirectory(prefix="upload-", dir=temp_root) as directory:
            folder = Path(directory)
            original = folder / f"original{extension}"
            size = await _save_temporary_upload(file, original)
            metadata, thumbnail, variants = process_file(original, folder, media_type, mime)

            storage_key = _key(base_key, original.name)
            s3_service.upload_file(original, storage_key, mime)
            uploaded_keys.append(storage_key)

            thumbnail_key = None
            if thumbnail:
                thumbnail_key = _key(base_key, thumbnail.name)
                s3_service.upload_file(thumbnail, thumbnail_key, "image/jpeg")
                uploaded_keys.append(thumbnail_key)

            variant_keys = {}
            for quality, variant_path in variants.items():
                key = _key(base_key, "variants", variant_path.name)
                s3_service.upload_file(variant_path, key, "video/mp4")
                uploaded_keys.append(key)
                variant_keys[quality] = key

            return MediaUploadResult(
                media_type=media_type, mime_type=mime, storage_key=storage_key,
                size=size, metadata=metadata, thumbnail_key=thumbnail_key,
                variants=variant_keys,
            )
    except Exception:
        if uploaded_keys:
            try:
                s3_service.delete_objects(uploaded_keys)
            except HTTPException:
                # A falha original é mais relevante; o serviço S3 já registrou a limpeza incompleta.
                pass
        raise


def _probe(path: Path) -> dict:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration,bit_rate:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels", "-of", "json", str(path)],
            capture_output=True, text=True, check=True, timeout=30,
        )
        return json.loads(result.stdout)
    except (FileNotFoundError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        raise HTTPException(503, "FFmpeg/ffprobe é necessário para processar áudio e vídeo") from exc


def process_file(path: Path, folder: Path, media_type: str, mime: str):
    metadata, thumbnail, variants = {}, None, {}
    if media_type == "image":
        if mime == "image/svg+xml":
            text = path.read_text(errors="ignore")[:500]
            if "<svg" not in text.lower():
                raise HTTPException(400, "SVG inválido")
            metadata = {"format": "SVG", "color_depth": None, "dpi": None, "exif": {}}
            thumbnail = folder / "thumbnail.jpg"
            Image.new("RGB", (480, 320), "#e8eef8").save(thumbnail, "JPEG", quality=85)
        else:
            try:
                with Image.open(path) as image:
                    image.verify()
                with Image.open(path) as image:
                    exif_raw = image.getexif()
                    exif = {ExifTags.TAGS.get(k, str(k)): str(v) for k, v in exif_raw.items() if ExifTags.TAGS.get(k, str(k)) in {"Model", "ExposureTime", "FNumber", "ISOSpeedRatings", "DateTimeOriginal", "GPSInfo"}}
                    metadata = {"width": image.width, "height": image.height, "color_depth": len(image.getbands()) * 8, "dpi": list(image.info.get("dpi", ())) or None, "exif": exif}
                    thumb = ImageOps.exif_transpose(image).convert("RGB")
                    thumb.thumbnail((480, 320))
                    thumbnail = folder / "thumbnail.jpg"
                    thumb.save(thumbnail, "JPEG", quality=85)
            except (OSError, ValueError) as exc:
                raise HTTPException(400, "Arquivo de imagem inválido ou corrompido") from exc
    else:
        probe = _probe(path)
        fmt = probe.get("format", {})
        streams = probe.get("streams", [])
        metadata = {"duration": float(fmt.get("duration") or 0), "bit_rate": int(fmt.get("bit_rate") or 0)}
        if media_type == "audio":
            stream = next((s for s in streams if s.get("codec_type") == "audio"), {})
            metadata.update({"codec": stream.get("codec_name"), "sample_rate": int(stream.get("sample_rate") or 0), "channels": stream.get("channels")})
        else:
            video = next((s for s in streams if s.get("codec_type") == "video"), {})
            audio = next((s for s in streams if s.get("codec_type") == "audio"), {})
            rate = video.get("r_frame_rate", "0/1").split("/")
            fps = round(float(rate[0]) / max(float(rate[1]), 1), 3)
            metadata.update({"width": video.get("width"), "height": video.get("height"), "fps": fps, "video_codec": video.get("codec_name"), "audio_codec": audio.get("codec_name")})
            thumbnail = folder / "thumbnail.jpg"
            try:
                subprocess.run(["ffmpeg", "-y", "-i", str(path), "-frames:v", "1", "-vf", "scale=480:-2", str(thumbnail)], capture_output=True, check=True, timeout=60)
                for quality, height in (("1080p", 1080), ("720p", 720), ("480p", 480)):
                    output = folder / f"{quality}.mp4"
                    subprocess.run(["ffmpeg", "-y", "-i", str(path), "-vf", f"scale=-2:{height}", "-c:v", "libx264", "-preset", "veryfast", "-c:a", "aac", "-movflags", "+faststart", str(output)], capture_output=True, check=True, timeout=1800)
                    variants[quality] = output
            except (FileNotFoundError, subprocess.SubprocessError) as exc:
                raise HTTPException(503, "Não foi possível gerar as versões do vídeo com FFmpeg") from exc
    return metadata, thumbnail, variants
