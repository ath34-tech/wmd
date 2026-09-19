import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

# Image types Gemini accepts, mapped to the extension we save them with.
EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/heic": ".heic",
    "image/heif": ".heif",
}
CHUNK_BYTES = 64 * 1024


async def save_upload(image: UploadFile) -> Path:
    """Save an uploaded image under a random name in the upload dir."""
    if image.content_type not in EXTENSIONS:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Unsupported image type; use one of: {', '.join(EXTENSIONS)}",
        )
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    path = upload_dir / f"{uuid.uuid4().hex}{EXTENSIONS[image.content_type]}"

    size = 0
    with path.open("wb") as out:
        while chunk := await image.read(CHUNK_BYTES):
            size += len(chunk)
            if size > settings.max_upload_bytes:
                break
            out.write(chunk)
    if size > settings.max_upload_bytes:
        path.unlink()
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"Image exceeds {settings.max_upload_bytes} bytes",
        )
    return path
