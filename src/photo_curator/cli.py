from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from loguru import logger

from photo_curator.config import Settings, ensure_dirs, load_settings
from photo_curator.db import Database
from photo_curator.pipeline_run import PipelineRun, write_run_artifact
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
    run_tracker = PipelineRun(db)
    try:
        target_roots = roots or [Path(root) for root in settings.default_roots]
        target_extensions = extensions or settings.extensions

        run_tracker.start(ingest_limit=settings.ingest_limit, ingest_strategy=settings.ingest_selection_strategy)

        discover_stats = discover_files(db, settings, roots=target_roots, extensions=target_extensions)
        run_tracker.update_stage(files_ingested=discover_stats.upserted, skipped=discover_stats.skipped)

        logger.info(
            "Discover complete: scanned={scanned} upserted={upserted} skipped={skipped} failed_db={failed_db} failed_processing={failed_proc}",
            scanned=discover_stats.scanned,
            upserted=discover_stats.upserted,
            skipped=discover_stats.skipped,
            failed_db=discover_stats.failed_db,
            failed_proc=discover_stats.failed_processing,
        )
    finally:
        _close_db(db)


@app.command("score-metrics")
def score_metrics_cmd(
    max_size: int = typer.Option(1280, "--max-size", help="Max side length for metric computation"),
    config: Optional[str] = typer.Option(None, "--config"),
) -> None:
    db, settings = _init_db(config)
    run_tracker = PipelineRun(db)
    try:
        run_tracker.start(nima_model_version="nima_style_v0")

        metrics_stats = score_metrics(db, max_size=max_size)
        run_tracker.update_stage(metrics_scored=metrics_stats.processed)

        run_id = run_tracker.complete()
        write_run_artifact(db, run_id, report_dir=settings.report_dir)

        logger.info("Metrics scored: {count} (run: {run_id})", count=metrics_stats.processed, run_id=run_id)
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
    run_tracker = PipelineRun(db)
    try:
        target_roots = roots or [Path(root) for root in settings.default_roots]
        target_extensions = extensions or settings.extensions

        # Start tracking this run
        run_tracker.start(
            nima_model_version="nima_style_v0",
            description_provider=(description_provider or settings.description_provider).strip().lower(),
            ingest_limit=settings.ingest_limit,
            ingest_strategy=settings.ingest_selection_strategy,
        )

        discover_stats = discover_files(
            db, settings, roots=target_roots, extensions=target_extensions
        )
        run_tracker.update_stage(files_ingested=discover_stats.upserted, skipped=discover_stats.skipped)

        metrics_stats = score_metrics(db, max_size=max_size)
        run_tracker.update_stage(metrics_scored=metrics_stats.processed)

        advanced_stats = run_advanced_runners(
            db,
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
        run_tracker.update_stage(nima_scored=advanced_stats.nima_processed, described=advanced_stats.described_processed)

        # Complete the run with score distributions stored in DB + artifact file
        run_id = run_tracker.complete()
        write_run_artifact(db, run_id, report_dir=settings.report_dir)

        logger.info("=" * 60)
        logger.info("Pipeline summary (run: {run_id}):", run_id=run_id)
        logger.info(
            "  Discovered: scanned={scanned} upserted={upserted} skipped={skipped} failed_db={failed_db} failed_processing={failed_proc}",
            scanned=discover_stats.scanned,
            upserted=discover_stats.upserted,
            skipped=discover_stats.skipped,
            failed_db=discover_stats.failed_db,
            failed_proc=discover_stats.failed_processing,
        )
        if discover_stats.failed_db > 0 or discover_stats.failed_processing > 0:
            logger.warning(
                "  DB failures: {db_fail} | Processing failures: {proc_fail}",
                db_fail=discover_stats.failed_db,
                proc_fail=discover_stats.failed_processing,
            )
        logger.info("  Metrics scored: {count}", count=metrics_stats.processed)
        logger.info("  NIMA scores generated: {nima}", nima=advanced_stats.nima_processed)
        logger.info("  Descriptions generated: {desc}", desc=advanced_stats.described_processed)
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
    run_tracker = PipelineRun(db)
    try:
        target_roots = roots or [Path(root) for root in settings.default_roots]
        target_extensions = extensions or settings.extensions

        run_tracker.start(
            nima_model_version="nima_style_v0",
            description_provider=settings.description_provider,
            ingest_limit=settings.ingest_limit,
            ingest_strategy=settings.ingest_selection_strategy,
        )

        discover_stats = discover_files(
            db, settings, roots=target_roots, extensions=target_extensions
        )
        run_tracker.update_stage(files_ingested=discover_stats.upserted, skipped=discover_stats.skipped)

        metrics_stats = score_metrics(db, max_size=max_size)
        run_tracker.update_stage(metrics_scored=metrics_stats.processed)

        run_id = run_tracker.complete()
        write_run_artifact(db, run_id, report_dir=settings.report_dir)

        logger.info(
            "Base ingest complete: upserted={upserted} metrics={metrics} (run: {run_id})",
            upserted=discover_stats.upserted,
            metrics=metrics_stats.processed,
            run_id=run_id,
        )
    finally:
        _close_db(db)


@app.command("score-nima")
def score_nima_cmd(
    config: Optional[str] = typer.Option(None, "--config"),
) -> None:
    db, settings = _init_db(config)
    run_tracker = PipelineRun(db)
    try:
        run_tracker.start(nima_model_version="nima_style_v0")

        stats = score_nima(db)
        run_tracker.update_stage(nima_scored=stats.processed)

        run_id = run_tracker.complete()
        write_run_artifact(db, run_id, report_dir=settings.report_dir)

        logger.info("NIMA runner complete: processed={processed} (run: {run_id})", processed=stats.processed, run_id=run_id)
    finally:
        _close_db(db)


@app.command("advanced-runner")
def advanced_runner_cmd(
    run_descriptions: bool = typer.Option(True, "--run-descriptions/--skip-descriptions"),
    model_name: str = typer.Option("basic-caption-v1", "--model-name"),
    description_provider: Optional[str] = typer.Option(None, "--description-provider"),
    lmstudio_timeout_seconds: Optional[float] = typer.Option(None, "--lmstudio-timeout-seconds"),
    config: Optional[str] = typer.Option(None, "--config"),
) -> None:
    db, settings = _init_db(config)
    run_tracker = PipelineRun(db)
    try:
        run_tracker.start(
            nima_model_version="nima_style_v0",
            description_provider=(description_provider or settings.description_provider).strip().lower(),
        )

        stats = run_advanced_runners(
            db,
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
        run_tracker.update_stage(nima_scored=stats.nima_processed, described=stats.described_processed)

        run_id = run_tracker.complete()
        write_run_artifact(db, run_id, report_dir=settings.report_dir)

        logger.info(
            "Advanced runner complete: nima={nima} descriptions={desc} (run: {run_id})",
            nima=stats.nima_processed,
            desc=stats.described_processed,
            run_id=run_id,
        )
    finally:
        _close_db(db)


if __name__ == "__main__":
    app()
