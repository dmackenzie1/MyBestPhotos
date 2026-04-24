from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from photo_curator.pipeline_v1.common import _iter_files
from photo_curator.pipeline_v1.selection import (
    _select_discovery_candidates,
    _should_skip_due_to_duplicate_cap,
)
from photo_curator.pipeline_v1.models import DescriptionOptions
from photo_curator.pipeline_v1.scoring_math import _compute_nima_style_score

if TYPE_CHECKING:
    from photo_curator.config import Settings
    from photo_curator.db import Database


def discover_files(db: "Database", settings: "Settings", roots: list[Path], extensions: list[str]):
    from photo_curator.pipeline_v1.discovery import discover_files as _discover_files

    return _discover_files(db, settings, roots, extensions)


def score_metrics(db: "Database", max_size: int = 1024):
    from photo_curator.pipeline_v1.metrics_stage import score_metrics as _score_metrics

    return _score_metrics(db, max_size=max_size)


def describe_images(
    db: "Database", model_name: str = "basic-caption-v1", options: DescriptionOptions | None = None
):
    from photo_curator.pipeline_v1.description_stage import describe_images as _describe_images

    return _describe_images(db, model_name=model_name, options=options)


def score_nima(
    db: "Database",
    *,
    max_size: int = 1024,
    clip_model: str | None = None,
    clip_device: str = "auto",
):
    from photo_curator.pipeline_v1.advanced_stage import score_nima as _score_nima

    return _score_nima(db, max_size=max_size, clip_model=clip_model, clip_device=clip_device)


def run_advanced_runners(
    db: "Database",
    *,
    run_descriptions: bool = True,
    description_model_name: str = "basic-caption-v1",
    description_options: DescriptionOptions | None = None,
    batch_size: int = 500,
    clip_model: str | None = None,
    clip_device: str = "auto",
    force_rescore_all: bool = False,
    defer_apply_until_complete: bool = False,
):
    from photo_curator.pipeline_v1.advanced_stage import (
        run_advanced_runners as _run_advanced_runners,
    )

    return _run_advanced_runners(
        db,
        run_descriptions=run_descriptions,
        description_model_name=description_model_name,
        description_options=description_options,
        batch_size=batch_size,
        clip_model=clip_model,
        clip_device=clip_device,
        force_rescore_all=force_rescore_all,
        defer_apply_until_complete=defer_apply_until_complete,
    )


__all__ = [
    "DescriptionOptions",
    "describe_images",
    "discover_files",
    "run_advanced_runners",
    "score_metrics",
    "score_nima",
    "_compute_nima_style_score",
    "_iter_files",
    "_select_discovery_candidates",
    "_should_skip_due_to_duplicate_cap",
]
