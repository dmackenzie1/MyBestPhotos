from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
from loguru import logger
import numpy as np
from tqdm import tqdm

from photo_curator.db import Database


def _existing_tables(db: Database, table_names: set[str]) -> set[str]:
    rows = db.fetchall(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = ANY(%s)
        """,
        (list(table_names),),
    )
    return {str(row[0]) for row in rows}


def _technical_mode(db: Database) -> str:
    legacy_required = {"photos", "metrics"}
    v1_required = {"files", "file_metrics"}
    existing = _existing_tables(db, legacy_required | v1_required)
    if legacy_required.issubset(existing):
        return "legacy"
    if v1_required.issubset(existing):
        return "v1"
    missing = sorted(v1_required - existing)
    raise RuntimeError(
        "Technical scoring requires either legacy tables (photos/metrics) or v1 tables "
        f"(files/file_metrics). Missing v1 tables: {', '.join(missing)}."
    )


@dataclass
class TechnicalStats:
    processed: int = 0


def _load_image(path: Path, max_size: int = 1024) -> np.ndarray | None:
    image = cv2.imread(str(path))
    if image is None:
        return None
    h, w = image.shape[:2]
    if max(h, w) > max_size:
        scale = max_size / max(h, w)
        image = cv2.resize(image, (int(w * scale), int(h * scale)))
    return image


def _metrics(image: np.ndarray) -> tuple[float, float, float, float, float]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    exposure_clip_hi = float(np.mean(gray >= 250))
    exposure_clip_lo = float(np.mean(gray <= 5))
    contrast = float(np.std(gray) / 255.0)
    noise_proxy = float(np.std(cv2.GaussianBlur(gray, (3, 3), 0) - gray))
    return sharpness, exposure_clip_hi, exposure_clip_lo, contrast, noise_proxy


def score_technical(db: Database, max_size: int = 1024, force: bool = False) -> TechnicalStats:
    mode = _technical_mode(db)
    if mode == "legacy":
        photos_sql = """
            SELECT id, path FROM photos
            {where_clause}
        """
        where_clause = "" if force else "WHERE id NOT IN (SELECT photo_id FROM metrics)"
    else:
        photos_sql = """
            SELECT id, source_root || '/' || relative_path AS path FROM files
            {where_clause}
        """
        where_clause = "" if force else "WHERE id NOT IN (SELECT file_id FROM file_metrics)"
    photos = db.fetchall(photos_sql.format(where_clause=where_clause))

    stats = TechnicalStats()
    for photo_id, path in tqdm(photos, desc="Scoring technical"):
        image = _load_image(Path(path), max_size=max_size)
        if image is None:
            logger.warning("Failed to load image for metrics: {path}", path=path)
            continue
        sharpness, clip_hi, clip_lo, contrast, noise = _metrics(image)
        if mode == "legacy":
            db.execute(
                """
                INSERT INTO metrics (
                    photo_id, sharpness, exposure_clip_hi, exposure_clip_lo, contrast, noise_proxy
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (photo_id) DO UPDATE SET
                    sharpness = EXCLUDED.sharpness,
                    exposure_clip_hi = EXCLUDED.exposure_clip_hi,
                    exposure_clip_lo = EXCLUDED.exposure_clip_lo,
                    contrast = EXCLUDED.contrast,
                    noise_proxy = EXCLUDED.noise_proxy,
                    created_at = now()
                """,
                (photo_id, sharpness, clip_hi, clip_lo, contrast, noise),
            )
        else:
            db.execute(
                """
                INSERT INTO file_metrics (
                    file_id,
                    blur_score,
                    brightness_score,
                    contrast_score,
                    noise_score,
                    technical_quality_score,
                    updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, now())
                ON CONFLICT (file_id) DO UPDATE SET
                    blur_score = EXCLUDED.blur_score,
                    brightness_score = EXCLUDED.brightness_score,
                    contrast_score = EXCLUDED.contrast_score,
                    noise_score = EXCLUDED.noise_score,
                    technical_quality_score = EXCLUDED.technical_quality_score,
                    updated_at = now()
                """,
                (
                    photo_id,
                    sharpness,
                    float(np.clip(1.0 - ((clip_hi + clip_lo) / 2.0), 0.0, 1.0)),
                    contrast,
                    noise,
                    float(
                        np.clip(
                            (contrast * 0.5) + (sharpness / (sharpness + 100.0)) * 0.5, 0.0, 1.0
                        )
                    ),
                ),
            )
        stats.processed += 1

    logger.info(
        "Technical scoring complete: mode={mode} processed={processed}",
        mode=mode,
        processed=stats.processed,
    )
    return stats
