from __future__ import annotations

from dataclasses import dataclass


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
    nima_processed: int = 0
    described_processed: int = 0


@dataclass(frozen=True)
class DescriptionOptions:
    provider: str = "basic"
    lmstudio_base_url: str = "http://192.168.10.64:1234/v1"
    lmstudio_model: str = "qwen3.6-35b-a3b"
    lmstudio_timeout_seconds: float = 60.0
