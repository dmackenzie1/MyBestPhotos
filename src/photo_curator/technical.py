from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
from loguru import logger
import numpy as np
from tqdm import tqdm

from photo_curator.db import Database


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
    photos = db.fetchall(
        """
        SELECT id, path FROM photos
        WHERE (%s) OR (id NOT IN (SELECT photo_id FROM metrics))
        """,
        (force,),
    )

    stats = TechnicalStats()
    for photo_id, path in tqdm(photos, desc="Scoring technical"):
        image = _load_image(Path(path), max_size=max_size)
        if image is None:
            logger.warning("Failed to load image for metrics: {path}", path=path)
            continue
        sharpness, clip_hi, clip_lo, contrast, noise = _metrics(image)
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
        stats.processed += 1

    logger.info("Technical scoring complete: processed={processed}", processed=stats.processed)
    return stats
