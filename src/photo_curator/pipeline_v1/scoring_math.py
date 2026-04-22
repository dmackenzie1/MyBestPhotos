from __future__ import annotations


def _derive_aesthetic_and_keep_scores(
    *,
    nima_score: float,
    technical_quality_score: float,
    blur_score: float,
) -> tuple[float, float]:
    aesthetic_score = max(0.0, min(1.0, (0.85 * nima_score) + (0.15 * (1.0 - blur_score))))
    keep_score = max(0.0, min(1.0, (0.60 * technical_quality_score) + (0.40 * aesthetic_score)))
    return aesthetic_score, keep_score


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
    aesthetic_score, keep_score = _derive_aesthetic_and_keep_scores(
        nima_score=nima_score,
        technical_quality_score=technical_quality_score,
        blur_score=blur_score,
    )
    return nima_score, aesthetic_score, keep_score
