from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import mimetypes
from pathlib import Path
import re
from typing import Iterable

import cv2
from loguru import logger
import numpy as np
from tqdm import tqdm

from photo_curator.config import Settings
from photo_curator.db import Database
from photo_curator.utils.hashing import sha256_file
from photo_curator.utils.image import SUPPORTED_EXTENSIONS, get_exif, open_image

DATE_RE = re.compile(r"(20\d{2})[-_]?([01]\d)[-_]?([0-3]\d)")


@dataclass
class DiscoverStats:
    scanned: int = 0
    upserted: int = 0
    skipped: int = 0


@dataclass
class StageStats:
    processed: int = 0


def _iter_files(roots: Iterable[Path], extensions: set[str]) -> Iterable[tuple[Path, Path]]:
    for root in roots:
        root = root.resolve()
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower().lstrip(".") not in extensions:
                continue
            yield root, path


def _parse_datetime_from_candidate(value: str) -> datetime | None:
    match = DATE_RE.search(value)
    if not match:
        return None
    year, month, day = [int(match.group(i)) for i in range(1, 4)]
    try:
        return datetime(year, month, day, tzinfo=timezone.utc)
    except ValueError:
        return None


def _resolve_taken_at(exif_datetime: str | None, path: Path) -> tuple[datetime, str]:
    if exif_datetime:
        cleaned = exif_datetime.replace(":", "-", 2)
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(cleaned, fmt).replace(tzinfo=timezone.utc), "exif"
            except ValueError:
                continue

    from_name = _parse_datetime_from_candidate(path.name)
    if from_name:
        return from_name, "filename"

    for part in path.parts:
        from_dir = _parse_datetime_from_candidate(part)
        if from_dir:
            return from_dir, "directory"

    return datetime.now(timezone.utc), "ingest_time"


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    text = str(value)
    if "/" in text:
        left, right = text.split("/", maxsplit=1)
        try:
            return float(left) / float(right)
        except (ValueError, ZeroDivisionError):
            return None
    try:
        return float(text)
    except ValueError:
        return None


def discover_files(db: Database, settings: Settings, roots: list[Path], extensions: list[str]) -> DiscoverStats:
    if not roots:
        raise ValueError("No roots provided. Set PHOTO_CURATOR_DEFAULT_ROOTS or pass --roots.")

    ext_set = {ext.lower().lstrip(".") for ext in extensions} or SUPPORTED_EXTENSIONS
    stats = DiscoverStats()

    for root, path in tqdm(list(_iter_files(roots, ext_set)), desc="Discovering"):
        stats.scanned += 1

        image = open_image(path)
        if image is None:
            stats.skipped += 1
            continue

        stat = path.stat()
        width, height = image.size
        exif = get_exif(image)

        exif_datetime = exif.get("DateTimeOriginal") or exif.get("DateTime")
        taken_at, taken_source = _resolve_taken_at(exif_datetime, path)
        relative_path = path.relative_to(root).as_posix()

        gps_info = exif.get("GPSInfo") if isinstance(exif.get("GPSInfo"), dict) else {}
        gps_lat = _to_float(gps_info.get("GPSLatitude")) if gps_info else None
        gps_lon = _to_float(gps_info.get("GPSLongitude")) if gps_info else None

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
                sha256_file(path),
                width,
                height,
                exif.get("Orientation"),
                taken_at,
                taken_source,
                exif.get("Make"),
                exif.get("Model"),
                gps_lat,
                gps_lon,
                json.dumps(exif, default=str),
            ),
        )
        stats.upserted += 1

    logger.info("File discovery complete: {stats}", stats=stats)
    return stats


def _load_image(path: Path, max_size: int = 1024) -> np.ndarray | None:
    image = cv2.imread(str(path))
    if image is None:
        return None
    h, w = image.shape[:2]
    if max(h, w) > max_size:
        scale = max_size / max(h, w)
        image = cv2.resize(image, (int(w * scale), int(h * scale)))
    return image


def _safe_norm(value: float, low: float, high: float) -> float:
    if high - low <= 0:
        return 0.0
    return max(0.0, min(1.0, (value - low) / (high - low)))


def _compute_metrics(image: np.ndarray) -> tuple[float, float, float, float, float, float, float, float]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    blur_score = 1.0 - _safe_norm(lap_var, 100.0, 1200.0)

    brightness = float(np.mean(gray) / 255.0)
    brightness_score = 1.0 - abs(brightness - 0.55)

    contrast_raw = float(np.std(gray) / 255.0)
    contrast_score = _safe_norm(contrast_raw, 0.08, 0.45)

    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).ravel()
    hist /= np.sum(hist) + 1e-8
    entropy = float(-np.sum(hist * np.log2(hist + 1e-12)) / 8.0)

    noise = float(np.std(gray - cv2.GaussianBlur(gray, (3, 3), 0)) / 255.0)
    noise_score = 1.0 - _safe_norm(noise, 0.02, 0.22)

    base_quality = (0.35 * (1.0 - blur_score)) + (0.25 * contrast_score) + (0.2 * brightness_score) + (0.2 * noise_score)
    print_6x8 = max(0.0, min(1.0, base_quality))
    print_8x10 = max(0.0, min(1.0, base_quality * 0.95))
    print_12x18 = max(0.0, min(1.0, base_quality * 0.9))

    return blur_score, brightness_score, contrast_score, entropy, noise_score, print_6x8, print_8x10, print_12x18


def score_metrics(db: Database, max_size: int = 1024) -> StageStats:
    rows = db.fetchall("SELECT id, source_root, relative_path FROM files ORDER BY id")
    stats = StageStats()

    for file_id, source_root, relative_path in tqdm(rows, desc="Metrics"):
        path = Path(source_root) / Path(relative_path)
        image = _load_image(path, max_size=max_size)
        if image is None:
            continue

        (
            blur_score,
            brightness_score,
            contrast_score,
            entropy_score,
            noise_score,
            print_6x8,
            print_8x10,
            print_12x18,
        ) = _compute_metrics(image)

        db.execute(
            """
            INSERT INTO file_metrics (
              file_id, blur_score, brightness_score, contrast_score, entropy_score, noise_score,
              print_score_6x8, print_score_8x10, print_score_12x18
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (file_id) DO UPDATE SET
              blur_score = EXCLUDED.blur_score,
              brightness_score = EXCLUDED.brightness_score,
              contrast_score = EXCLUDED.contrast_score,
              entropy_score = EXCLUDED.entropy_score,
              noise_score = EXCLUDED.noise_score,
              print_score_6x8 = EXCLUDED.print_score_6x8,
              print_score_8x10 = EXCLUDED.print_score_8x10,
              print_score_12x18 = EXCLUDED.print_score_12x18,
              updated_at = now()
            """,
            (
                file_id,
                blur_score,
                brightness_score,
                contrast_score,
                entropy_score,
                noise_score,
                print_6x8,
                print_8x10,
                print_12x18,
            ),
        )
        stats.processed += 1

    logger.info("Metric scoring complete: processed={count}", count=stats.processed)
    return stats


def describe_images(db: Database, model_name: str = "basic-caption-v1") -> StageStats:
    rows = db.fetchall(
        """
        SELECT f.id, f.filename, f.camera_make, f.camera_model, f.photo_taken_at,
               m.print_score_12x18, m.blur_score, m.brightness_score, m.contrast_score
        FROM files f
        LEFT JOIN file_metrics m ON m.file_id = f.id
        ORDER BY f.id
        """
    )

    stats = StageStats()
    for row in tqdm(rows, desc="Descriptions"):
        (
            file_id,
            filename,
            camera_make,
            camera_model,
            photo_taken_at,
            print_12x18,
            blur_score,
            brightness_score,
            contrast_score,
        ) = row

        quality_hint = "good"
        if print_12x18 is not None:
            if print_12x18 >= 0.85:
                quality_hint = "excellent"
            elif print_12x18 < 0.6:
                quality_hint = "fair"

        description_text = (
            f"Photo {filename} captured"
            + (f" on {photo_taken_at.date()}" if photo_taken_at else "")
            + (f" with {camera_make} {camera_model}" if camera_make or camera_model else "")
            + f". Overall technical quality looks {quality_hint}."
        )

        description_json = {
            "quality_hint": quality_hint,
            "camera_make": camera_make,
            "camera_model": camera_model,
            "scores": {
                "print_12x18": print_12x18,
                "blur": blur_score,
                "brightness": brightness_score,
                "contrast": contrast_score,
            },
            "categories": [],
        }

        db.execute(
            """
            INSERT INTO file_descriptions (file_id, model_name, description_text, description_json)
            VALUES (%s, %s, %s, %s::jsonb)
            ON CONFLICT (file_id) DO UPDATE SET
              model_name = EXCLUDED.model_name,
              description_text = EXCLUDED.description_text,
              description_json = EXCLUDED.description_json,
              updated_at = now()
            """,
            (file_id, model_name, description_text, json.dumps(description_json)),
        )
        stats.processed += 1

    logger.info("Description stage complete: processed={count}", count=stats.processed)
    return stats
