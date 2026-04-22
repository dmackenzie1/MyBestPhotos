from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import tomllib
from typing import Annotated, Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, EnvSettingsSource, NoDecode, SettingsConfigDict


class CompatEnvSettingsSource(EnvSettingsSource):
    def prepare_field_value(
        self, field_name: str, field: Any, value: Any, value_is_complex: bool
    ) -> Any:
        if field_name == "default_roots" and isinstance(value, str):
            return value
        return super().prepare_field_value(field_name, field, value, value_is_complex)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PHOTO_CURATOR_",
        env_file=".env",
        extra="ignore",
    )

    db_dsn: str = "postgresql://localhost:5432/photo_curator"
    cache_dir: str = ".cache"
    thumbs_dir: str = ".cache/thumbs"
    log_dir: str = "logs"
    report_dir: str = "reports"
    config_path: str = "config.toml"

    # Keep env parsing for default_roots in our validator/source so plain paths and CSV values
    # work without requiring JSON list syntax in PHOTO_CURATOR_DEFAULT_ROOTS.
    default_roots: Annotated[list[str], NoDecode] = []
    extensions: list[str] = ["jpg", "jpeg", "png", "webp"]
    thumbnail_size: int = 512
    batch_size: int = 32
    clip_model: str = "ViT-B-32"
    clip_weights_path: str = ""
    embedding_device: str = "auto"
    description_provider: str = "basic"
    lmstudio_base_url: str = "http://127.0.0.1:1234/v1"
    lmstudio_model: str = "qwen2.5-vl-7b-instruct"
    lmstudio_timeout_seconds: float = 60.0

    aesthetics_method: str = "aesthetic_v0"

    weights_technical: float = 0.4
    weights_aesthetic: float = 0.6
    similarity_threshold: float = 0.88
    lambda_penalty: float = 0.15

    @field_validator("default_roots", mode="before")
    @classmethod
    def _coerce_default_roots(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            if text.startswith("["):
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError:
                    return []
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
                return []
            return [part.strip() for part in text.split(",") if part.strip()]
        return value

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        compat_env_settings = CompatEnvSettingsSource(settings_cls)
        return (compat_env_settings, dotenv_settings, init_settings, file_secret_settings)


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

    if "PHOTO_CURATOR_DEFAULT_ROOTS" not in os.environ:
        ingest_roots_csv = os.getenv("PHOTO_INGEST_ROOTS")
        if ingest_roots_csv is not None:
            flat["default_roots"] = ingest_roots_csv

    settings = Settings(**flat)
    return LoadedConfig(settings=settings, raw=data)


def ensure_dirs(settings: Settings) -> None:
    Path(settings.cache_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.thumbs_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.log_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.report_dir).mkdir(parents=True, exist_ok=True)
