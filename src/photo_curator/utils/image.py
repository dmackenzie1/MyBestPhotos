from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger
from PIL import Image, ExifTags


SUPPORTED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


def open_image(path: Path) -> Image.Image | None:
    try:
        return Image.open(path)
    except OSError as exc:
        logger.warning("Failed to open image {path}: {error}", path=path, error=str(exc))
        return None


def get_exif(image: Image.Image) -> dict[str, Any]:
    try:
        exif = image.getexif()
        return {ExifTags.TAGS.get(k, str(k)): v for k, v in exif.items()}
    except Exception:  # noqa: BLE001
        return {}
