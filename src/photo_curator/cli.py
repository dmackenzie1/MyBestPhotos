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
    run_advanced_runners,
    score_metrics,
    score_nima,
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

        discover_stats = discover_files(
            db, settings, roots=target_roots, extensions=target_extensions
        )
        metrics_stats = score_metrics(db, max_size=max_size)
        advanced_stats = run_advanced_runners(
            db,
            nima_batch_size=200,
            nima_refresh_all=False,
            nima_model_version="nima_style_v0",
            run_descriptions=True,
            description_model_name=model_name,
            description_options=DescriptionOptions(
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

        logger.info("=" * 60)
        logger.info("Pipeline summary:")
        logger.info(
            "  Discovered: %d scanned, %d upserted, %d skipped",
            discover_stats.scanned,
            discover_stats.upserted,
            discover_stats.skipped,
        )
        if discover_stats.failed_db > 0 or discover_stats.failed_processing > 0:
            logger.warning(
                "  DB failures: %d | Processing failures: %d",
                discover_stats.failed_db,
                discover_stats.failed_processing,
            )
        logger.info("  Metrics scored: %d", metrics_stats.processed)
        logger.info("  NIMA scores generated: %d", advanced_stats.nima_processed)
        logger.info("  Descriptions generated: %d", advanced_stats.described_processed)
        logger.info("=" * 60)

        logger.info("Pipeline complete.")
    finally:
        _close_db(db)


@app.command("base-ingest")
def base_ingest_cmd(
    roots: list[Path] = typer.Option([], "--roots", help="Root folders to scan"),
    extensions: list[str] = typer.Option([], "--extensions", help="File extensions"),
    max_size: int = typer.Option(1280, "--max-size"),
    config: Optional[str] = typer.Option(None, "--config"),
) -> None:
    db, settings = _init_db(config)
    try:
        target_roots = roots or [Path(root) for root in settings.default_roots]
        target_extensions = extensions or settings.extensions
        discover_stats = discover_files(
            db, settings, roots=target_roots, extensions=target_extensions
        )
        metrics_stats = score_metrics(db, max_size=max_size)
        logger.info(
            "Base ingest complete: upserted=%d metrics=%d",
            discover_stats.upserted,
            metrics_stats.processed,
        )
    finally:
        _close_db(db)


@app.command("score-nima")
def score_nima_cmd(
    batch_size: int = typer.Option(100, "--batch-size", min=1),
    refresh_all: bool = typer.Option(False, "--refresh-all"),
    model_version: str = typer.Option("nima_style_v0", "--model-version"),
    config: Optional[str] = typer.Option(None, "--config"),
) -> None:
    db, _settings = _init_db(config)
    try:
        stats = score_nima(
            db,
            batch_size=batch_size,
            refresh_all=refresh_all,
            nima_model_version=model_version,
        )
        logger.info("NIMA runner complete: processed=%d", stats.processed)
    finally:
        _close_db(db)


@app.command("advanced-runner")
def advanced_runner_cmd(
    nima_batch_size: int = typer.Option(100, "--nima-batch-size", min=1),
    nima_refresh_all: bool = typer.Option(False, "--nima-refresh-all"),
    nima_model_version: str = typer.Option("nima_style_v0", "--nima-model-version"),
    run_descriptions: bool = typer.Option(True, "--run-descriptions/--skip-descriptions"),
    model_name: str = typer.Option("basic-caption-v1", "--model-name"),
    description_provider: Optional[str] = typer.Option(None, "--description-provider"),
    lmstudio_timeout_seconds: Optional[float] = typer.Option(None, "--lmstudio-timeout-seconds"),
    config: Optional[str] = typer.Option(None, "--config"),
) -> None:
    db, settings = _init_db(config)
    try:
        stats = run_advanced_runners(
            db,
            nima_batch_size=nima_batch_size,
            nima_refresh_all=nima_refresh_all,
            nima_model_version=nima_model_version,
            run_descriptions=run_descriptions,
            description_model_name=model_name,
            description_options=DescriptionOptions(
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
        logger.info(
            "Advanced runner complete: nima=%d descriptions=%d",
            stats.nima_processed,
            stats.described_processed,
        )
    finally:
        _close_db(db)


if __name__ == "__main__":
    app()
