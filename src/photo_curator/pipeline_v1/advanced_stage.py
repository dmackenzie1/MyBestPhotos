from __future__ import annotations

from pathlib import Path

import cv2
from loguru import logger
import numpy as np
from tqdm import tqdm

from photo_curator.db import Database
from photo_curator.pipeline_v1.common import _load_image
from photo_curator.pipeline_v1.description_stage import describe_images
from photo_curator.pipeline_v1.metrics_stage import _compute_metrics
from photo_curator.pipeline_v1.models import AdvancedRunnerStats, DescriptionOptions, StageStats
from photo_curator.pipeline_v1.scoring_math import _compute_nima_style_score


def _composition_balance_score(gray) -> float:
    height, width = gray.shape[:2]
    if height == 0 or width == 0:
        return 0.0

    grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    saliency = cv2.magnitude(grad_x, grad_y)
    total = float(saliency.sum()) + 1e-6

    yy, xx = np.indices(gray.shape, dtype=np.float32)
    cx = float(np.sum(xx * saliency) / total)
    cy = float(np.sum(yy * saliency) / total)

    thirds = [
        (width / 3.0, height / 3.0),
        (2.0 * width / 3.0, height / 3.0),
        (width / 3.0, 2.0 * height / 3.0),
        (2.0 * width / 3.0, 2.0 * height / 3.0),
    ]
    min_distance = min(np.hypot(cx - tx, cy - ty) for tx, ty in thirds)
    max_distance = float(np.hypot(width, height))
    return max(0.0, min(1.0, 1.0 - (min_distance / (max_distance + 1e-6))))


def _resolve_or_compute_metrics(
    db_row: tuple[object, ...],
    image,
) -> tuple[float, float, float, float, float]:
    blur_score, brightness_score, contrast_score, entropy_score, technical_quality_score = db_row
    if all(value is not None for value in db_row):
        return (
            float(blur_score),
            float(brightness_score),
            float(contrast_score),
            float(entropy_score),
            float(technical_quality_score),
        )

    (
        computed_blur_score,
        computed_brightness_score,
        computed_contrast_score,
        computed_entropy_score,
        _noise_score,
        computed_technical_quality_score,
        _print_6x8,
        _print_8x10,
        _print_12x18,
    ) = _compute_metrics(image)
    return (
        computed_blur_score,
        computed_brightness_score,
        computed_contrast_score,
        computed_entropy_score,
        computed_technical_quality_score,
    )


def score_nima(
    db: Database,
    *,
    max_size: int = 1024,
    batch_size: int = 100,
    refresh_all: bool = False,
    nima_model_version: str = "nima_style_v0",
) -> StageStats:
    where_clause = "TRUE" if refresh_all else "fm.nima_score IS NULL"
    rows = db.fetchall(
        f"""
        SELECT f.id, f.source_root, f.relative_path,
               fm.blur_score, fm.brightness_score, fm.contrast_score, fm.entropy_score, fm.technical_quality_score
        FROM files f
        LEFT JOIN file_metrics fm ON fm.file_id = f.id
        WHERE {where_clause}
        ORDER BY COALESCE(fm.advanced_metadata_updated_at, fm.updated_at, f.updated_at, f.created_at) ASC NULLS FIRST,
                 f.id ASC
        LIMIT %s
        """,
        (batch_size,),
    )

    stats = StageStats()
    for row in tqdm(rows, desc="NIMA"):
        (
            file_id,
            source_root,
            relative_path,
            blur_score,
            brightness_score,
            contrast_score,
            entropy_score,
            technical_quality_score,
        ) = row
        path = Path(source_root) / Path(relative_path)
        image = _load_image(path, max_size=max_size)
        if image is None:
            logger.warning("Could not load image for NIMA score, skipping: {path}", path=path)
            continue

        (
            blur_score,
            brightness_score,
            contrast_score,
            entropy_score,
            technical_quality_score,
        ) = _resolve_or_compute_metrics(
            (blur_score, brightness_score, contrast_score, entropy_score, technical_quality_score),
            image,
        )
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        composition_balance_score = _composition_balance_score(gray)
        nima_score, aesthetic_score, keep_score = _compute_nima_style_score(
            blur_score=blur_score,
            brightness_score=brightness_score,
            contrast_score=contrast_score,
            entropy_score=entropy_score,
            technical_quality_score=technical_quality_score,
            composition_balance_score=composition_balance_score,
        )

        db.execute(
            """
            INSERT INTO file_metrics (
              file_id, nima_score, aesthetic_score, keep_score,
              nima_model_version, advanced_metadata_updated_at
            ) VALUES (%s, %s, %s, %s, %s, now())
            ON CONFLICT (file_id) DO UPDATE SET
              nima_score = EXCLUDED.nima_score,
              aesthetic_score = EXCLUDED.aesthetic_score,
              keep_score = EXCLUDED.keep_score,
              nima_model_version = EXCLUDED.nima_model_version,
              advanced_metadata_updated_at = now(),
              updated_at = now()
            """,
            (file_id, nima_score, aesthetic_score, keep_score, nima_model_version),
        )
        stats.processed += 1

    logger.info(
        "NIMA stage complete: processed={processed}, refresh_all={refresh_all}",
        processed=stats.processed,
        refresh_all=refresh_all,
    )
    return stats


def run_advanced_runners(
    db: Database,
    *,
    nima_batch_size: int = 100,
    nima_refresh_all: bool = False,
    nima_model_version: str = "nima_style_v0",
    run_descriptions: bool = True,
    description_model_name: str = "basic-caption-v1",
    description_options: DescriptionOptions | None = None,
) -> AdvancedRunnerStats:
    nima_stats = score_nima(
        db,
        batch_size=nima_batch_size,
        refresh_all=nima_refresh_all,
        nima_model_version=nima_model_version,
    )
    describe_stats = StageStats()
    if run_descriptions:
        describe_stats = describe_images(
            db,
            model_name=description_model_name,
            options=description_options,
        )

    return AdvancedRunnerStats(
        nima_processed=nima_stats.processed,
        described_processed=describe_stats.processed,
    )
