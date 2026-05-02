from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".webm"}


class InvalidUploadError(ValueError):
    pass


async def save_upload(file: UploadFile) -> Path:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise InvalidUploadError(f"Unsupported file type. Allowed: {allowed}")

    settings.local_storage_dir.mkdir(parents=True, exist_ok=True)
    target_path = settings.local_storage_dir / f"{uuid4().hex}{suffix}"

    total = 0
    with target_path.open("wb") as destination:
        while chunk := await file.read(1024 * 1024):
            total += len(chunk)
            if total > settings.max_upload_bytes:
                target_path.unlink(missing_ok=True)
                raise InvalidUploadError(f"File is larger than {settings.max_upload_mb} MB")
            destination.write(chunk)

    return target_path
