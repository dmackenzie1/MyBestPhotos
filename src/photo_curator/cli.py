from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from loguru import logger

from photo_curator.aesthetics import score_aesthetic
from photo_curator.config import Settings, ensure_dirs, load_settings
from photo_curator.db import Database
from photo_curator.dedup import dedup
from photo_curator.embeddings import embed
from photo_curator.ingest import ingest
from photo_curator.report import export_reports
from photo_curator.select_top import select_top
from photo_curator.technical import score_technical
from photo_curator.utils.logging import configure_logging

app = typer.Typer(help="Local-only photo curator pipeline")


def _init_db(config_path: Optional[str]) -> tuple[Database, Settings]:
    loaded = load_settings(config_path)
    settings = loaded.settings
    ensure_dirs(settings)
    configure_logging(settings.log_dir)
    db = Database(settings.db_dsn)
    db.check()
    return db, settings


@app.command()
def ingest_cmd(
    roots: list[Path] = typer.Option(..., "--roots", help="Root folders to scan"),
    extensions: list[str] = typer.Option([], "--extensions", help="File extensions"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    force: bool = typer.Option(False, "--force"),
    config: Optional[str] = typer.Option(None, "--config"),
) -> None:
    db, settings = _init_db(config)
    roots = roots or [Path(root) for root in settings.default_roots]
    ext = extensions or settings.extensions
    ingest(db, settings, roots=roots, extensions=ext, dry_run=dry_run, force=force)


@app.command("score-technical")
def score_technical_cmd(
    max_size: int = typer.Option(1024, "--max-size"),
    force: bool = typer.Option(False, "--force"),
    config: Optional[str] = typer.Option(None, "--config"),
) -> None:
    db, _settings = _init_db(config)
    score_technical(db, max_size=max_size, force=force)


@app.command()
def embed_cmd(
    model: str = typer.Option("ViT-B-32", "--model"),
    weights_path: Optional[str] = typer.Option(None, "--weights-path"),
    batch_size: int = typer.Option(32, "--batch-size"),
    device: str = typer.Option("auto", "--device"),
    force: bool = typer.Option(False, "--force"),
    config: Optional[str] = typer.Option(None, "--config"),
) -> None:
    db, settings = _init_db(config)
    weights = weights_path or settings.clip_weights_path or None
    embed(
        db,
        settings,
        model_name=model,
        weights_path=weights,
        batch_size=batch_size,
        device=device,
        force=force,
    )


@app.command("score-aesthetic")
def score_aesthetic_cmd(
    model: str = typer.Option("ViT-B-32", "--model"),
    weights_path: Optional[str] = typer.Option(None, "--weights-path"),
    device: str = typer.Option("auto", "--device"),
    config: Optional[str] = typer.Option(None, "--config"),
) -> None:
    db, settings = _init_db(config)
    weights = weights_path or settings.clip_weights_path or None
    score_aesthetic(db, model_name=model, weights_path=weights, device=device)


@app.command()
def dedup_cmd(
    threshold: int = typer.Option(6, "--threshold"),
    config: Optional[str] = typer.Option(None, "--config"),
) -> None:
    db, settings = _init_db(config)
    dedup(db, thumbs_dir=settings.thumbs_dir, threshold=threshold)


@app.command("select-top")
def select_top_cmd(
    top_n: int = typer.Option(100, "--top-n"),
    output: Optional[str] = typer.Option(None, "--output"),
    copy: bool = typer.Option(False, "--copy"),
    link: bool = typer.Option(False, "--link"),
    config: Optional[str] = typer.Option(None, "--config"),
) -> None:
    db, settings = _init_db(config)
    result = select_top(db, settings, top_n=top_n)
    export_reports(
        db,
        run_id=result.run_id,
        report_dir=settings.report_dir,
        thumbs_dir=settings.thumbs_dir,
        output_dir=output,
        copy_files=copy,
        link_files=link,
    )


@app.command()
def pipeline(
    roots: list[Path] = typer.Option(..., "--roots", help="Root folders to scan"),
    top_n: int = typer.Option(100, "--top-n"),
    extensions: list[str] = typer.Option([], "--extensions"),
    weights_path: Optional[str] = typer.Option(None, "--weights-path"),
    config: Optional[str] = typer.Option(None, "--config"),
) -> None:
    db, settings = _init_db(config)
    ext = extensions or settings.extensions
    weights = weights_path or settings.clip_weights_path or None

    ingest(db, settings, roots=roots, extensions=ext, dry_run=False, force=False)
    score_technical(db)
    embed(
        db,
        settings,
        model_name=settings.clip_model,
        weights_path=weights,
        batch_size=settings.batch_size,
        device=settings.embedding_device,
        force=False,
    )
    score_aesthetic(db, model_name=settings.clip_model, weights_path=weights, device=settings.embedding_device)
    dedup(db, thumbs_dir=settings.thumbs_dir)
    result = select_top(db, settings, top_n=top_n)
    export_reports(
        db,
        run_id=result.run_id,
        report_dir=settings.report_dir,
        thumbs_dir=settings.thumbs_dir,
        output_dir=None,
        copy_files=False,
    )
    logger.info("Pipeline complete: run_id={run_id}", run_id=result.run_id)
