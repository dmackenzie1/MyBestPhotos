from __future__ import annotations

import json
import mimetypes
from pathlib import Path

from loguru import logger
from tqdm import tqdm

from photo_curator.config import Settings
from photo_curator.db import Database
from photo_curator.pipeline_v1.common import (
    _resolve_taken_at,
    _sanitize_exif,
    _sanitize_str,
    _to_float,
)
from photo_curator.pipeline_v1.models import DiscoverStats
from photo_curator.pipeline_v1.selection import (
    _select_discovery_candidates,
    _should_skip_due_to_duplicate_cap,
)
from photo_curator.utils.hashing import sha256_file
from photo_curator.utils.image import SUPPORTED_EXTENSIONS, get_exif, open_image


def discover_files(
    db: Database, settings: Settings, roots: list[Path], extensions: list[str]
) -> DiscoverStats:
    if not roots:
        raise ValueError(
            "No roots provided. Set PHOTO_CURATOR_DEFAULT_ROOTS (or PHOTO_INGEST_ROOTS) or pass --roots."
        )

    ext_set = {ext.lower().lstrip(".") for ext in extensions} or SUPPORTED_EXTENSIONS
    stats = DiscoverStats()

    stats.eligible, selected_candidates = _select_discovery_candidates(
        roots,
        ext_set,
        ingest_limit=settings.ingest_limit,
        strategy=settings.ingest_selection_strategy,
        seed=settings.ingest_selection_seed,
    )
    stats.selected = len(selected_candidates)

    logger.info(
        "Discover candidate selection: eligible={eligible} selected={selected} limit={limit} strategy={strategy}",
        eligible=stats.eligible,
        selected=stats.selected,
        limit=settings.ingest_limit,
        strategy=settings.ingest_selection_strategy,
    )

    for root, path in tqdm(selected_candidates, desc="Discovering"):
        stats.scanned += 1
        relative_path = path.relative_to(root).as_posix()

        try:
            logger.info("Processing file: {path}", path=path.name)

            image = open_image(path)
            if image is None:
                logger.warning("Could not open image, skipping: {path}", path=path.name)
                stats.skipped += 1
                continue

            stat = path.stat()
            width, height = image.size
            exif = get_exif(image)

            exif_datetime = exif.get("DateTimeOriginal") or exif.get("DateTime")
            taken_at, taken_source = _resolve_taken_at(exif_datetime, path)

            gps_info = exif.get("GPSInfo") if isinstance(exif.get("GPSInfo"), dict) else {}
            gps_lat = _to_float(gps_info.get("GPSLatitude")) if gps_info else None
            gps_lon = _to_float(gps_info.get("GPSLongitude")) if gps_info else None

            sanitized_exif = _sanitize_exif(exif)
            exif_json_str = json.dumps(sanitized_exif, default=str)

            try:
                file_hash = sha256_file(path)
                existing_rows = db.fetchall(
                    "SELECT id FROM files WHERE source_root = %s AND relative_path = %s",
                    (str(root), relative_path),
                )

                filename_count_row = db.fetchall(
                    "SELECT COUNT(*) FROM files WHERE filename = %s",
                    (path.name,),
                )
                filename_count = int(filename_count_row[0][0]) if filename_count_row else 0

                sha_count_row = db.fetchall(
                    "SELECT COUNT(*) FROM files WHERE sha256 = %s", (file_hash,)
                )
                sha_count = int(sha_count_row[0][0]) if sha_count_row else 0

                if _should_skip_due_to_duplicate_cap(
                    existing_path_record=bool(existing_rows),
                    filename_count=filename_count,
                    sha_count=sha_count,
                    duplicate_cap=settings.duplicate_cap_per_filename_or_sha,
                ):
                    logger.info(
                        "Skipping insert for {filename}: duplicate cap reached (filename_count={filename_count}, sha_count={sha_count}, cap={cap})",
                        filename=path.name,
                        filename_count=filename_count,
                        sha_count=sha_count,
                        cap=settings.duplicate_cap_per_filename_or_sha,
                    )
                    stats.skipped += 1
                    continue

                db.execute(
                    """
                    INSERT INTO files (
                      source_root, relative_path, filename, extension, mime_type, file_size_bytes,
                      sha256, width, height, orientation, photo_taken_at, photo_taken_at_source,
                      camera_make, camera_model, gps_lat, gps_lon, exif_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                    ON CONFLICT (source_root, relative_path) DO UPDATE SET
                      filename = EXCLUDED.filename,
                      extension = EXCLUDED.extension,
                      mime_type = EXCLUDED.mime_type,
                      file_size_bytes = EXCLUDED.file_size_bytes,
                      sha256 = EXCLUDED.sha256,
                      width = EXCLUDED.width,
                      height = EXCLUDED.height,
                      orientation = EXCLUDED.orientation,
                      photo_taken_at = EXCLUDED.photo_taken_at,
                      photo_taken_at_source = EXCLUDED.photo_taken_at_source,
                      camera_make = EXCLUDED.camera_make,
                      camera_model = EXCLUDED.camera_model,
                      gps_lat = EXCLUDED.gps_lat,
                      gps_lon = EXCLUDED.gps_lon,
                      exif_json = EXCLUDED.exif_json,
                      updated_at = now()
                    """,
                    (
                        str(root),
                        relative_path,
                        path.name,
                        path.suffix.lower().lstrip("."),
                        mimetypes.guess_type(path.name)[0],
                        stat.st_size,
                        file_hash,
                        width,
                        height,
                        exif.get("Orientation"),
                        taken_at,
                        taken_source,
                        _sanitize_str(exif.get("Make")),
                        _sanitize_str(exif.get("Model")),
                        gps_lat,
                        gps_lon,
                        exif_json_str,
                    ),
                )
                logger.info(
                    "File inserted/updated: {filename} size={size}B dims={w}x{h}",
                    filename=path.name,
                    size=stat.st_size,
                    w=width,
                    h=height,
                )
                stats.upserted += 1
            except Exception as db_exc:
                logger.error(
                    "DB insert failed for {filename}: {error}",
                    filename=path.name,
                    error=str(db_exc),
                )
                stats.failed_db += 1

        except Exception as file_exc:
            logger.error(
                "File processing failed for {path}: {error}",
                path=path.name,
                error=str(file_exc),
            )
            stats.failed_processing += 1
    return stats
