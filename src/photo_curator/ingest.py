from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from loguru import logger
from tqdm import tqdm

from photo_curator.config import Settings
from photo_curator.db import Database
from photo_curator.utils.hashing import sha256_file
from photo_curator.utils.image import SUPPORTED_EXTENSIONS, get_exif, open_image


@dataclass
class IngestStats:
    scanned: int = 0
    inserted: int = 0
    skipped: int = 0


def _iter_files(roots: Iterable[Path], extensions: set[str]) -> Iterable[Path]:
    for root in roots:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower().lstrip(".") not in extensions:
                continue
            yield path


def _thumbnail_path(settings: Settings, file_hash: str) -> Path:
    return Path(settings.thumbs_dir) / f"{file_hash}.jpg"


def ingest(
    db: Database,
    settings: Settings,
    roots: list[Path],
    extensions: list[str],
    dry_run: bool = False,
    force: bool = False,
) -> IngestStats:
    if not roots:
        raise ValueError("No roots provided. Use --roots or set default_roots in config.")

    ext_set = {ext.lower().lstrip(".") for ext in extensions} or SUPPORTED_EXTENSIONS
    stats = IngestStats()

    files = list(_iter_files(roots, ext_set))
    for path in tqdm(files, desc="Ingesting"):
        stats.scanned += 1
        suffix = path.suffix.lower().lstrip(".")
        if suffix in {"heic", "heif"} and suffix not in SUPPORTED_EXTENSIONS:
            logger.warning("HEIC/HEIF not supported in this build. Skipping {path}.", path=path)
            stats.skipped += 1
            continue

        file_stat = path.stat()
        mtime = datetime.fromtimestamp(file_stat.st_mtime, tz=timezone.utc)
        size_bytes = file_stat.st_size

        existing = db.fetchall(
            "SELECT id FROM photos WHERE path = %s AND mtime = %s AND size_bytes = %s",
            (str(path), mtime, size_bytes),
        )
        if existing and not force:
            stats.skipped += 1
            continue

        file_hash = sha256_file(path)
        image = open_image(path)
        if image is None:
            stats.skipped += 1
            continue

        width, height = image.size
        exif = get_exif(image)
        exif_datetime = exif.get("DateTimeOriginal") or exif.get("DateTime")
        camera_make = exif.get("Make")
        camera_model = exif.get("Model")
        lens = exif.get("LensModel") or exif.get("Lens")
        iso = exif.get("ISOSpeedRatings")
        shutter = exif.get("ExposureTime")
        aperture = exif.get("FNumber")
        focal_length = exif.get("FocalLength")

        thumb_path = _thumbnail_path(settings, file_hash)
        if not thumb_path.exists() and not dry_run:
            image.thumbnail((settings.thumbnail_size, settings.thumbnail_size))
            image.convert("RGB").save(thumb_path, "JPEG", quality=90)

        if dry_run:
            stats.inserted += 1
            continue

        db.execute(
            """
            INSERT INTO photos (
                path, sha256, mtime, size_bytes, width, height, exif_datetime,
                camera_make, camera_model, lens, iso, shutter, aperture, focal_length
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (path) DO UPDATE SET
                sha256 = EXCLUDED.sha256,
                mtime = EXCLUDED.mtime,
                size_bytes = EXCLUDED.size_bytes,
                width = EXCLUDED.width,
                height = EXCLUDED.height,
                exif_datetime = EXCLUDED.exif_datetime,
                camera_make = EXCLUDED.camera_make,
                camera_model = EXCLUDED.camera_model,
                lens = EXCLUDED.lens,
                iso = EXCLUDED.iso,
                shutter = EXCLUDED.shutter,
                aperture = EXCLUDED.aperture,
                focal_length = EXCLUDED.focal_length,
                updated_at = now()
            """,
            (
                str(path),
                file_hash,
                mtime,
                size_bytes,
                width,
                height,
                exif_datetime,
                camera_make,
                camera_model,
                lens,
                iso,
                str(shutter) if shutter else None,
                str(aperture) if aperture else None,
                str(focal_length) if focal_length else None,
            ),
        )
        stats.inserted += 1

    logger.info(
        "Ingest complete: scanned={scanned}, inserted={inserted}, skipped={skipped}",
        scanned=stats.scanned,
        inserted=stats.inserted,
        skipped=stats.skipped,
    )
    return stats
