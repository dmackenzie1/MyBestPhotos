from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from loguru import logger

from photo_curator.config import Settings, ensure_dirs, load_settings
from photo_curator.db import Database
from photo_curator.pipeline_v1 import (
    DescriptionOptions,
    describe_images,
    discover_files,
    score_metrics,
)
from photo_curator.utils.logging import configure_logging

app = typer.Typer(help="Photo curation ingestion and enrichment pipeline")


def _init_db(config_path: Optional[str]) -> tuple[Database, Settings]:
    loaded = load_settings(config_path)
    settings = loaded.settings
    ensure_dirs(settings)
    configure_logging(settings.log_dir)
    db = Database(settings.db_dsn)
    db.check()
    return db, settings


def _close_db(db: Database) -> None:
    db.close()


@app.command("discover")
def discover_cmd(
    roots: list[Path] = typer.Option([], "--roots", help="Root folders to scan"),
    extensions: list[str] = typer.Option([], "--extensions", help="File extensions"),
    config: Optional[str] = typer.Option(None, "--config"),
) -> None:
    db, settings = _init_db(config)
    try:
        target_roots = roots or [Path(root) for root in settings.default_roots]
        target_extensions = extensions or settings.extensions
        discover_files(db, settings, roots=target_roots, extensions=target_extensions)
    finally:
        _close_db(db)


@app.command("score-metrics")
def score_metrics_cmd(
    max_size: int = typer.Option(1280, "--max-size", help="Max side length for metric computation"),
    config: Optional[str] = typer.Option(None, "--config"),
) -> None:
    db, _settings = _init_db(config)
    try:
        score_metrics(db, max_size=max_size)
    finally:
        _close_db(db)


@app.command("describe")
def describe_cmd(
    model_name: str = typer.Option("basic-caption-v1", "--model-name"),
    description_provider: Optional[str] = typer.Option(None, "--description-provider"),
    lmstudio_timeout_seconds: Optional[float] = typer.Option(None, "--lmstudio-timeout-seconds"),
    config: Optional[str] = typer.Option(None, "--config"),
) -> None:
    db, settings = _init_db(config)
    try:
        describe_images(
            db,
            model_name=model_name,
            options=DescriptionOptions(
                provider=(description_provider or settings.description_provider).strip().lower(),
                lmstudio_base_url=settings.lmstudio_base_url,
                lmstudio_model=settings.lmstudio_model,
                lmstudio_timeout_seconds=(
                    lmstudio_timeout_seconds
                    if lmstudio_timeout_seconds is not None
                    else settings.lmstudio_timeout_seconds
                ),
            ),
        )
    finally:
        _close_db(db)


@app.command("pipeline")
def pipeline_cmd(
    roots: list[Path] = typer.Option([], "--roots", help="Root folders to scan"),
    extensions: list[str] = typer.Option([], "--extensions", help="File extensions"),
    max_size: int = typer.Option(1280, "--max-size"),
    model_name: str = typer.Option("basic-caption-v1", "--model-name"),
    description_provider: Optional[str] = typer.Option(None, "--description-provider"),
    lmstudio_timeout_seconds: Optional[float] = typer.Option(None, "--lmstudio-timeout-seconds"),
    config: Optional[str] = typer.Option(None, "--config"),
) -> None:
    db, settings = _init_db(config)
    try:
        target_roots = roots or [Path(root) for root in settings.default_roots]
        target_extensions = extensions or settings.extensions

        discover_files(db, settings, roots=target_roots, extensions=target_extensions)
        score_metrics(db, max_size=max_size)
        describe_images(
            db,
            model_name=model_name,
            options=DescriptionOptions(
                provider=(description_provider or settings.description_provider).strip().lower(),
                lmstudio_base_url=settings.lmstudio_base_url,
                lmstudio_model=settings.lmstudio_model,
                lmstudio_timeout_seconds=(
                    lmstudio_timeout_seconds
                    if lmstudio_timeout_seconds is not None
                    else settings.lmstudio_timeout_seconds
                ),
            ),
        )

        logger.info("Pipeline complete.")
    finally:
        _close_db(db)


if __name__ == "__main__":
    app()
