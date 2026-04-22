from __future__ import annotations

from pathlib import Path

import cv2
from loguru import logger
import numpy as np
from tqdm import tqdm

from photo_curator.db import Database
from photo_curator.pipeline_run import ScoreDistribution, _compute_distribution

from photo_curator.pipeline_v1.common import _load_image, _safe_norm
from photo_curator.pipeline_v1.models import StageStats


def _compute_metrics(
    image: np.ndarray,
) -> tuple[float, float, float, float, float, float, float, float, float]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    blur_score = 1.0 - _safe_norm(lap_var, 100.0, 1200.0)

    brightness = float(np.mean(gray) / 255.0)
    # Most photos are naturally brighter than mid-gray; use a wider optimal range
    # and non-linear mapping to spread scores more evenly
    brightness_deviation = abs(brightness - 0.65)
    brightness_score = max(0.0, min(1.0, 1.0 - (brightness_deviation / 0.35)))

    contrast_raw = float(np.std(gray) / 255.0)
    contrast_score = _safe_norm(contrast_raw, 0.08, 0.45)

    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).ravel()
    hist /= np.sum(hist) + 1e-8
    entropy = float(-np.sum(hist * np.log2(hist + 1e-12)) / 8.0)

    noise = float(np.std(gray - cv2.GaussianBlur(gray, (3, 3), 0)) / 255.0)
    # High-frequency band analysis: measure variance in the highest frequency bands
    # after applying a stronger low-pass filter to isolate fine-grained noise patterns
    smoothed = cv2.GaussianBlur(gray.astype(np.float64), (15, 15), 3.0)
    high_freq = np.abs(gray.astype(np.float64) - smoothed)
    noise_proxy = float(np.std(high_freq)) / 255.0
    # Use a wider normalization range since modern cameras produce very low noise values
    noise_score = 1.0 - _safe_norm(noise_proxy, 0.001, 0.08)

    technical_quality_score = max(
        0.0,
        min(
            1.0,
            (0.30 * (1.0 - blur_score))
            + (0.20 * contrast_score)
            + (0.20 * brightness_score)
            + (0.15 * entropy)
            + (0.15 * noise_score),
        ),
    )
    print_6x8 = max(0.0, min(1.0, technical_quality_score))
    print_8x10 = max(0.0, min(1.0, technical_quality_score * 0.95))
    print_12x18 = max(0.0, min(1.0, technical_quality_score * 0.9))

    return (
        blur_score,
        brightness_score,
        contrast_score,
        entropy,
        noise_score,
        technical_quality_score,
        print_6x8,
        print_8x10,
        print_12x18,
    )


def score_metrics(db: Database, max_size: int = 1024) -> StageStats:
    rows = db.fetchall("SELECT id, source_root, relative_path FROM files ORDER BY id")
    stats = StageStats()

    for file_id, source_root, relative_path in tqdm(rows, desc="Metrics"):
        path = Path(source_root) / Path(relative_path)
        logger.info("Scoring metrics: file_id={id} path={path}", id=file_id, path=path)

        image = _load_image(path, max_size=max_size)
        if image is None:
            logger.warning("Could not load image for metrics, skipping: {path}", path=path)
            continue

        (
            blur_score,
            brightness_score,
            contrast_score,
            entropy_score,
            noise_score,
            technical_quality_score,
            print_6x8,
            print_8x10,
            print_12x18,
        ) = _compute_metrics(image)

        try:
            db.execute(
                """
                INSERT INTO file_metrics (
                  file_id, blur_score, brightness_score, contrast_score, entropy_score, noise_score,
                  technical_quality_score, print_score_6x8, print_score_8x10, print_score_12x18
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (file_id) DO UPDATE SET
                  blur_score = EXCLUDED.blur_score,
                  brightness_score = EXCLUDED.brightness_score,
                  contrast_score = EXCLUDED.contrast_score,
                  entropy_score = EXCLUDED.entropy_score,
                  noise_score = EXCLUDED.noise_score,
                  technical_quality_score = EXCLUDED.technical_quality_score,
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
                    technical_quality_score,
                    print_6x8,
                    print_8x10,
                    print_12x18,
                ),
            )
            logger.info(
                "Metrics scored: file_id={id} blur={blur:.3f} brightness={bright:.3f} contrast={contrast:.3f}",
                id=file_id,
                blur=blur_score,
                bright=brightness_score,
                contrast=contrast_score,
            )
            stats.processed += 1
        except Exception as exc:
            logger.error(
                "Metrics DB insert failed for file_id={id}: {error}", id=file_id, error=str(exc)
            )

    # Log score distribution summary after metrics stage
    _log_metrics_distribution(db, stats.processed)

    logger.info("Metric scoring complete: processed={count}", count=stats.processed)
    return stats


def _log_metrics_distribution(db: Database, processed_count: int) -> None:
    """Log score distributions for the metrics fields after a run."""
    if processed_count == 0:
        logger.info("Score distribution: (no files scored)")
        return

    fields = [
        ("blur_score", "Blur"),
        ("brightness_score", "Brightness"),
        ("contrast_score", "Contrast"),
        ("entropy_score", "Entropy"),
        ("noise_score", "Noise"),
        ("technical_quality_score", "Technical Quality"),
    ]

    logger.info("=" * 80)
    logger.info("Metrics score distribution (processed={count})", count=processed_count)
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

    # Check for NULL counts in metrics fields
    null_fields = [
        ("blur_score", "Blur"),
        ("brightness_score", "Brightness"),
        ("contrast_score", "Contrast"),
        ("entropy_score", "Entropy"),
        ("noise_score", "Noise"),
        ("technical_quality_score", "Technical Quality"),
    ]

    null_counts = {}
    for col, name in null_fields:
        row = db.fetchall(f"SELECT COUNT(*) FROM file_metrics WHERE {col} IS NULL")
        if row and int(row[0][0]) > 0:
            null_counts[name] = int(row[0][0])

    if null_counts:
        logger.info("  NULL counts: {nulls}", nulls=", ".join(f"{n}={c}" for n, c in null_counts.items()))
