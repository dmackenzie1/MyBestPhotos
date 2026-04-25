from __future__ import annotations

import re
from dataclasses import dataclass

_VISION_MODEL_PATTERNS = (
    r"llava",
    r"moondream",
    r"bakllava",
    r"qwen2\.5[-_]vl",
    r"qwen2[-_]vl",
    r"vision",
)


def is_vision_model(model_name: str) -> bool:
    return any(re.search(pat, model_name, re.IGNORECASE) for pat in _VISION_MODEL_PATTERNS)


@dataclass
class DiscoverStats:
    eligible: int = 0
    selected: int = 0
    scanned: int = 0
    upserted: int = 0
    skipped: int = 0
    failed_db: int = 0
    failed_processing: int = 0


@dataclass
class StageStats:
    processed: int = 0


@dataclass
class AdvancedRunnerStats:
    clip_processed: int = 0
    described_processed: int = 0


@dataclass(frozen=True)
class DescriptionOptions:
    provider: str = "basic"
    lmstudio_base_url: str = "http://localhost:1234/v1"
    lmstudio_model: str = "qwen3.5-9b"
    lmstudio_timeout_seconds: float = 60.0
