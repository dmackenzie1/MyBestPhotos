from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import tomllib
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PHOTO_CURATOR_",
        env_file=".env",
        extra="ignore",
    )

    db_dsn: str = "postgresql://photo_curator:photo_curator@localhost:5432/photo_curator"
    cache_dir: str = ".cache"
    thumbs_dir: str = ".cache/thumbs"
    log_dir: str = "logs"
    report_dir: str = "reports"
    config_path: str = "config.toml"

    default_roots: list[str] = []
    extensions: list[str] = ["jpg", "jpeg", "png", "webp"]
    thumbnail_size: int = 512
    batch_size: int = 32
    clip_model: str = "ViT-B-32"
    clip_weights_path: str = ""
    embedding_device: str = "auto"

    aesthetics_method: str = "aesthetic_v0"

    weights_technical: float = 0.4
    weights_aesthetic: float = 0.6
    similarity_threshold: float = 0.88
    lambda_penalty: float = 0.15

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (env_settings, dotenv_settings, init_settings, file_secret_settings)


@dataclass(frozen=True)
class LoadedConfig:
    settings: Settings
    raw: dict[str, Any]


def load_settings(config_path: str | None = None) -> LoadedConfig:
    env_path = os.getenv("PHOTO_CURATOR_CONFIG_PATH")
    path = Path(config_path or env_path or "config.toml")
    data: dict[str, Any] = {}
    if path.exists():
        with path.open("rb") as handle:
            data = tomllib.load(handle)

    flat: dict[str, Any] = {}
    for section in data.values():
        if isinstance(section, dict):
            flat.update(section)

    settings = Settings(**flat)
    return LoadedConfig(settings=settings, raw=data)


def ensure_dirs(settings: Settings) -> None:
    Path(settings.cache_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.thumbs_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.log_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.report_dir).mkdir(parents=True, exist_ok=True)
