from __future__ import annotations

from pathlib import Path

import cv2
from loguru import logger
import numpy as np
from tqdm import tqdm

from photo_curator.db import Database
from photo_curator.pipeline_run import _compute_distribution

from photo_curator.nima.inference import assess_quality
from photo_curator.pipeline_v1.common import _load_image
from photo_curator.pipeline_v1.description_stage import describe_images
from photo_curator.pipeline_v1.metrics_stage import _compute_metrics
from photo_curator.pipeline_v1.models import AdvancedRunnerStats, DescriptionOptions, StageStats


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
) -> StageStats:
    _BATCH_SIZE = 500
    nima_model_version = "nima_real_v1"

    stats = StageStats()
    while True:
        rows = db.fetchall(
            """
            SELECT f.id, f.source_root, f.relative_path,
                   fm.blur_score, fm.brightness_score, fm.contrast_score, fm.entropy_score, fm.technical_quality_score
            FROM files f
            LEFT JOIN file_metrics fm ON fm.file_id = f.id
            WHERE fm.nima_score IS NULL OR fm.nima_model_version != %s
            ORDER BY COALESCE(fm.advanced_metadata_updated_at, fm.updated_at, f.updated_at, f.created_at) ASC NULLS FIRST,
                     f.id ASC
            LIMIT %s
            """,
            (nima_model_version, _BATCH_SIZE),
        )

        if not rows:
            break

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

            # Real NIMA inference: returns (mean_normalized_to_0_1, std)
            nima_mean, nima_std = assess_quality(image)

            # Blend real NIMA score with composition balance signal.
            # Composition balance provides supplementary structural guidance.
            nima_spread = max(0.0, min(1.0, 0.85 * nima_mean + 0.15 * composition_balance_score))

            # Aesthetic score: NIMA primary + blur resistance (sharp photos look more aesthetic)
            blur_resistance = 1.0 - blur_score
            aesthetic_raw = (0.80 * nima_spread) + (0.20 * blur_resistance)
            aesthetic_spread = max(0.0, min(1.0, aesthetic_raw ** 0.75))

            # Keep score: combined technical quality + aesthetics for ranking workflows
            keep_raw = (0.65 * technical_quality_score) + (0.35 * aesthetic_spread)
            keep_spread = max(0.0, min(1.0, keep_raw ** 0.8))

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
                (file_id, nima_spread, aesthetic_spread, keep_spread, nima_model_version),
            )
            stats.processed += 1

    logger.info(
        "NIMA stage complete: processed={processed}",
        processed=stats.processed,
    )
    return stats


def run_advanced_runners(
    db: Database,
    *,
    run_descriptions: bool = True,
    description_model_name: str = "basic-caption-v1",
    description_options: DescriptionOptions | None = None,
) -> AdvancedRunnerStats:
    nima_stats = score_nima(db)
    describe_stats = StageStats()
    if run_descriptions:
        describe_stats = describe_images(
            db,
            model_name=description_model_name,
            options=description_options,
        )

    # Log advanced score distributions after all stages complete
    _log_advanced_distribution(db)

    return AdvancedRunnerStats(
        nima_processed=nima_stats.processed,
        described_processed=describe_stats.processed,
    )


def _log_advanced_distribution(db: Database) -> None:
    """Log score distributions for advanced scores (NIMA, aesthetic, keep, curation, semantic_relevance)."""
    fields = [
        ("nima_score", "NIMA Score"),
        ("aesthetic_score", "Aesthetic Score"),
        ("keep_score", "Keep Score"),
        ("curation_score", "Curation Score"),
        ("semantic_relevance_score", "Semantic Relevance"),
    ]

    logger.info("=" * 80)
    logger.info("Advanced score distribution")
    logger.info("-" * 80)

    for col, name in fields:
        rows = db.fetchall(f"SELECT {col} FROM file_metrics WHERE {col} IS NOT NULL")
        values = [float(r[0]) for r in rows if r[0] is not None]
        dist = _compute_distribution(values)

        logger.info(
            "  {name}  n={count}  min={min_val:.4f}  p25={p25:.4f}  median={median:.4f}  p75={p75:.4f}  p90={p90:.4f}  max={max_val:.4f}  stddev={stddev:.4f}",
            name=name,
            count=dist.count,
            min_val=dist.min_val,
            p25=dist.p25,
            median=dist.median,
            p75=dist.p75,
            p90=dist.p90,
            max_val=dist.max_val,
            stddev=dist.stddev,
        )

        if dist.count > 0 and dist.stddev < 0.05:
            logger.warning(
                "  !! {name} has very low spread (stddev={stddev:.4f}) — scores may be too compressed",
                name=name,
                stddev=dist.stddev,
            )

    # Check for NULL counts in advanced fields
    null_fields = [
        ("nima_score", "NIMA"),
        ("aesthetic_score", "Aesthetic"),
        ("keep_score", "Keep"),
        ("curation_score", "Curation"),
        ("semantic_relevance_score", "Semantic Relevance"),
    ]

    null_counts = {}
    for col, name in null_fields:
        row = db.fetchall(f"SELECT COUNT(*) FROM file_metrics WHERE {col} IS NULL")
        if row and int(row[0][0]) > 0:
            null_counts[name] = int(row[0][0])

    if null_counts:
        logger.info("  NULL counts: {nulls}", nulls=", ".join(f"{n}={c}" for n, c in null_counts.items()))
