from __future__ import annotations


def _compute_nima_style_score(
    *,
    blur_score: float,
    brightness_score: float,
    contrast_score: float,
    entropy_score: float,
    technical_quality_score: float,
    composition_balance_score: float,
) -> tuple[float, float, float]:
    nima_score = max(
        0.0,
        min(
            1.0,
            (0.35 * technical_quality_score)
            + (0.20 * contrast_score)
            + (0.15 * brightness_score)
            + (0.15 * entropy_score)
            + (0.15 * composition_balance_score),
        ),
    )
    aesthetic_score = max(0.0, min(1.0, (0.80 * nima_score) + (0.20 * (1.0 - blur_score))))
    keep_score = max(0.0, min(1.0, (0.65 * technical_quality_score) + (0.35 * aesthetic_score)))
    return nima_score, aesthetic_score, keep_score
