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
    # Linear weighted base score
    nima_base = (0.35 * technical_quality_score) + (0.20 * contrast_score) + (0.15 * brightness_score) + (0.15 * entropy_score) + (0.15 * composition_balance_score)

    # Non-linear spread: use power function to widen the distribution
    # This amplifies differences between high and low quality images
    nima_spread = max(0.0, min(1.0, nima_base ** 0.7))

    # Aesthetic score combines NIMA with blur resistance (sharp photos look more aesthetic)
    blur_resistance = 1.0 - blur_score
    aesthetic_raw = (0.80 * nima_spread) + (0.20 * blur_resistance)
    aesthetic_spread = max(0.0, min(1.0, aesthetic_raw ** 0.75))

    # Keep score: combined technical quality + aesthetics for ranking workflows
    keep_raw = (0.65 * technical_quality_score) + (0.35 * aesthetic_spread)
    keep_spread = max(0.0, min(1.0, keep_raw ** 0.8))

    return nima_spread, aesthetic_spread, keep_spread
