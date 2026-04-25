from __future__ import annotations

# Tuned weights based on analysis documented in docs/score-data-analysis.md.
CLIP_AESTHETIC_WEIGHT = 0.85
COMPOSITION_BALANCE_WEIGHT = 0.15
AESTHETIC_NIMA_WEIGHT = 0.82
AESTHETIC_BLUR_RESISTANCE_WEIGHT = 0.18
AESTHETIC_POWER_CURVE = 0.9
KEEP_TECHNICAL_WEIGHT = 0.45
KEEP_AESTHETIC_WEIGHT = 0.55
KEEP_POWER_CURVE = 0.9
CURATION_AESTHETIC_WEIGHT = 0.4
CURATION_KEEP_WEIGHT = 0.3
CURATION_TECHNICAL_WEIGHT = 0.2
CURATION_SEMANTIC_WEIGHT = 0.1


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def compute_keep_score(technical_quality: float, aesthetic_spread: float) -> float:
    keep_raw = (KEEP_TECHNICAL_WEIGHT * technical_quality) + (
        KEEP_AESTHETIC_WEIGHT * aesthetic_spread
    )
    return _clamp01(keep_raw**KEEP_POWER_CURVE)


def compute_clip_aesthetic(
    clip_score: float,
    composition_balance_score: float,
    blur_score: float,
    technical_quality_score: float,
) -> tuple[float, float, float]:
    nima_spread = _clamp01(
        (CLIP_AESTHETIC_WEIGHT * clip_score)
        + (COMPOSITION_BALANCE_WEIGHT * composition_balance_score)
    )
    blur_resistance = 1.0 - blur_score
    aesthetic_raw = (AESTHETIC_NIMA_WEIGHT * nima_spread) + (
        AESTHETIC_BLUR_RESISTANCE_WEIGHT * blur_resistance
    )
    aesthetic_spread = _clamp01(aesthetic_raw**AESTHETIC_POWER_CURVE)
    keep_spread = compute_keep_score(technical_quality_score, aesthetic_spread)
    return nima_spread, aesthetic_spread, keep_spread


def compute_curation_score(
    aesthetic: float, keep: float, tech_quality: float, semantic_relevance: float
) -> float:
    curation = (
        (CURATION_AESTHETIC_WEIGHT * aesthetic)
        + (CURATION_KEEP_WEIGHT * keep)
        + (CURATION_TECHNICAL_WEIGHT * tech_quality)
        + (CURATION_SEMANTIC_WEIGHT * semantic_relevance)
    )
    return _clamp01(curation)
