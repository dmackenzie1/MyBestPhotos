from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from loguru import logger

from photo_curator.db import Database


@dataclass
class ScoreDistribution:
    """Computed distribution stats for a single score field."""
    min_val: float = 0.0
    max_val: float = 1.0
    median: float = 0.5
    p25: float = 0.25
    p75: float = 0.75
    p90: float = 0.90
    stddev: float = 0.0
    count: int = 0


@dataclass
class PipelineRunStats:
    """Aggregated stats for a pipeline run."""
    run_id: str = ""
    nima_model_version: str = "nima_style_v0"
    description_provider: str = "basic"
    description_model_name: str = "basic-caption-v1"
    ingest_limit: int = 0
    ingest_strategy: str = "first"

    total_files_ingested: int = 0
    total_metrics_scored: int = 0
    total_nima_scored: int = 0
    total_described: int = 0
    total_skipped: int = 0
    total_failed: int = 0

    score_distributions: dict[str, ScoreDistribution] = field(default_factory=dict)


def _percentile(sorted_values: list[float], p: float) -> float:
    """Compute the p-th percentile from a sorted list (p in [0,1])."""
    if not sorted_values:
        return 0.0
    n = len(sorted_values)
    k = p * (n - 1)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_values[int(k)]
    d0 = sorted_values[f] * (c - k)
    d1 = sorted_values[c] * (k - f)
    return d0 + d1


def _compute_distribution(values: list[float]) -> ScoreDistribution:
    """Compute distribution stats from raw values."""
    if not values:
        return ScoreDistribution()

    arr = np.array(values, dtype=np.float64)
    sorted_vals = sorted(values)
    n = len(sorted_vals)

    return ScoreDistribution(
        min_val=float(arr.min()),
        max_val=float(arr.max()),
        median=float(np.median(arr)),
        p25=_percentile(sorted_vals, 0.25),
        p75=_percentile(sorted_vals, 0.75),
        p90=_percentile(sorted_vals, 0.90),
        stddev=float(np.std(arr, ddof=1) if n > 1 else 0.0),
        count=n,
    )


def _score_field_name(field: str) -> tuple[str, str]:
    """Map a score field name to (db_column_prefix, display_name)."""
    mapping = {
        "blur": ("blur", "Blur"),
        "brightness": ("brightness", "Brightness"),
        "contrast": ("contrast", "Contrast"),
        "entropy": ("entropy", "Entropy"),
        "noise": ("noise", "Noise"),
        "technical_quality": ("technical_quality", "Technical Quality"),
        "nima": ("nima", "NIMA Score"),
        "aesthetic": ("aesthetic", "Aesthetic Score"),
        "keep": ("keep", "Keep Score"),
        "curation": ("curation", "Curation Score"),
        "semantic_relevance": ("semantic_relevance", "Semantic Relevance"),
    }
    return mapping.get(field, (field, field))


def _log_distribution(name: str, dist: ScoreDistribution) -> None:
    """Log a score distribution to console in a human-readable format."""
    if dist.count == 0:
        logger.info("  %-25s  (no data)", name=name)
        return

    logger.info(
        "  {name}  n={count}  min={min_val:.4f}  p25={p25:.4f}  median={median:.4f}  p75={p75:.4f}  p90={p90:.4f}  max={max_val:.4f}  stddev={stddev:.4f}",
        name=name,
        count=dist.count,
        min_val=dist.min_val,
        p25=dist.p25,
        median=dist.median,
        p75=dist.p75,
        p90=dist.p90,
        max_val=dist.max_val,
        stddev=dist.stddev,
    )


class PipelineRun:
    """Manages a single pipeline run's lifecycle in the database."""

    def __init__(self, db: Database) -> None:
        self.db = db
        self.stats = PipelineRunStats()
        self._run_id: str | None = None

    @property
    def run_id(self) -> str:
        if not self._run_id:
            raise RuntimeError("PipelineRun has not been started. Call start() first.")
        return self._run_id

    def start(
        self,
        nima_model_version: str = "nima_style_v0",
        description_provider: str = "basic",
        description_model_name: str = "basic-caption-v1",
        ingest_limit: int = 0,
        ingest_strategy: str = "first",
    ) -> None:
        """Create a new pipeline run record in the database."""
        self.stats = PipelineRunStats(
            nima_model_version=nima_model_version,
            description_provider=description_provider,
            description_model_name=description_model_name,
            ingest_limit=ingest_limit,
            ingest_strategy=ingest_strategy,
        )

        # Generate run_id before inserting (DB default also generates one, but we want it in stats)
        import uuid
        self._run_id = str(uuid.uuid4())
        self.stats.run_id = self._run_id

        self.db.execute(
            """
            INSERT INTO pipeline_runs (run_id, status, nima_model_version,
                description_provider, description_model_name, ingest_limit, ingest_strategy)
            VALUES (%s, 'running', %s, %s, %s, %s, %s)
            """,
            (
                self._run_id,
                self.stats.nima_model_version,
                self.stats.description_provider,
                self.stats.description_model_name,
                self.stats.ingest_limit,
                self.stats.ingest_strategy,
            ),
        )

        logger.info("Pipeline run started: {run_id}", run_id=self.run_id)

    def update_stage(
        self,
        files_ingested: int | None = None,
        metrics_scored: int | None = None,
        nima_scored: int | None = None,
        described: int | None = None,
        skipped: int | None = None,
        failed: int | None = None,
    ) -> None:
        """Update accumulated stage counts for the current run."""
        if files_ingested is not None:
            self.stats.total_files_ingested += files_ingested
        if metrics_scored is not None:
            self.stats.total_metrics_scored += metrics_scored
        if nima_scored is not None:
            self.stats.total_nima_scored += nima_scored
        if described is not None:
            self.stats.total_described += described
        if skipped is not None:
            self.stats.total_skipped += skipped
        if failed is not None:
            self.stats.total_failed += failed

    def compute_and_store_score_distributions(self) -> dict[str, ScoreDistribution]:
        """Query file_metrics for score distributions and store them in the run record."""
        # Collect raw values from DB for each score field
        fields = [
            "blur_score",
            "brightness_score",
            "contrast_score",
            "entropy_score",
            "noise_score",
            "technical_quality_score",
            "nima_score",
            "aesthetic_score",
            "keep_score",
            "curation_score",
            "semantic_relevance_score",
        ]

        field_names = {
            "blur_score": "blur",
            "brightness_score": "brightness",
            "contrast_score": "contrast",
            "entropy_score": "entropy",
            "noise_score": "noise",
            "technical_quality_score": "technical_quality",
            "nima_score": "nima",
            "aesthetic_score": "aesthetic",
            "keep_score": "keep",
            "curation_score": "curation",
            "semantic_relevance_score": "semantic_relevance",
        }

        for col in fields:
            rows = self.db.fetchall(
                f"SELECT {col} FROM file_metrics WHERE {col} IS NOT NULL"
            )
            values = [float(r[0]) for r in rows if r[0] is not None]
            dist = _compute_distribution(values)
            self.stats.score_distributions[field_names[col]] = dist

        # Log distributions to console
        logger.info("=" * 80)
        logger.info("Score distribution summary (run: {run_id})", run_id=self.run_id)
        logger.info("-" * 80)
        for name, dist in self.stats.score_distributions.items():
            display_name = _score_field_name(name)[1]
            _log_distribution(display_name, dist)

        # Check for compression/clustering issues
        for name, dist in self.stats.score_distributions.items():
            if dist.count > 0 and dist.stddev < 0.05:
                display_name = _score_field_name(name)[1]
                logger.warning(
                    "  !! {name} has very low spread (stddev={stddev:.4f}) — scores may be too compressed",
                    name=display_name,
                    stddev=dist.stddev,
                )

        # Store distributions in the database
        self._store_distributions()

        return self.stats.score_distributions

    def _store_distributions(self) -> None:
        """Write score distribution stats to pipeline_runs table."""
        update_fields = []
        params = []

        for field_name, dist in self.stats.score_distributions.items():
            prefix = f"{field_name}_"
            attr_map = {"min": "min_val", "max": "max_val"}
            for stat_name in ["min", "max", "median", "p25", "p75", "p90", "stddev"]:
                col = f"{prefix}{stat_name}"
                attr = attr_map.get(stat_name, stat_name)
                val = getattr(dist, attr)
                update_fields.append(f"{col} = %s")
                params.append(val)

        # Also store total counts
        for count_field in [
            ("total_files_ingested", self.stats.total_files_ingested),
            ("total_metrics_scored", self.stats.total_metrics_scored),
            ("total_nima_scored", self.stats.total_nima_scored),
            ("total_described", self.stats.total_described),
            ("total_skipped", self.stats.total_skipped),
            ("total_failed", self.stats.total_failed),
        ]:
            update_fields.append(f"{count_field[0]} = %s")
            params.append(count_field[1])

        # Add notes about score spread
        low_spread = [
            _score_field_name(name)[1]
            for name, dist in self.stats.score_distributions.items()
            if dist.count > 0 and dist.stddev < 0.05
        ]
        notes_parts: list[str] = []
        if low_spread:
            notes_parts.append(f"LOW_SPREAD: {', '.join(low_spread)}")

        # Count files with NULL scores for each field
        null_counts = {}
        for col in ["nima_score", "aesthetic_score", "keep_score", "curation_score", "semantic_relevance_score"]:
            row = self.db.fetchall(f"SELECT COUNT(*) FROM file_metrics WHERE {col} IS NULL")
            if row:
                null_counts[col] = int(row[0][0])

        if null_counts:
            notes_parts.append(
                f"NULL_SCORES: nima={null_counts.get('nima_score', 0)} aesthetic={null_counts.get('aesthetic_score', 0)} "
                f"keep={null_counts.get('keep_score', 0)} curation={null_counts.get('curation_score', 0)} "
                f"semantic_relevance={null_counts.get('semantic_relevance_score', 0)}"
            )

        if notes_parts:
            update_fields.append("notes = %s")
            params.append("; ".join(notes_parts))

        if not update_fields:
            return

        sql = f"UPDATE pipeline_runs SET {', '.join(update_fields)}, completed_at = now() WHERE run_id = %s"
        params.append(self.run_id)
        self.db.execute(sql, tuple(params))

    def complete(
        self,
        status: str = "completed",
        notes: str | None = None,
    ) -> str:
        """Mark the pipeline run as completed and return the run_id."""
        # Compute distributions if not already done
        if not self.stats.score_distributions:
            self.compute_and_store_score_distributions()

        update_fields = [f"status = '{status}'", "completed_at = now()"]
        params: list[Any] = []

        for count_field in [
            ("total_files_ingested", self.stats.total_files_ingested),
            ("total_metrics_scored", self.stats.total_metrics_scored),
            ("total_nima_scored", self.stats.total_nima_scored),
            ("total_described", self.stats.total_described),
            ("total_skipped", self.stats.total_skipped),
            ("total_failed", self.stats.total_failed),
        ]:
            update_fields.append(f"{count_field[0]} = %s")
            params.append(count_field[1])

        if notes:
            existing_notes = notes or ""
            update_fields.append("notes = %s")
            params.append(existing_notes)

        sql = f"UPDATE pipeline_runs SET {', '.join(update_fields)} WHERE run_id = %s"
        params.append(self.run_id)
        self.db.execute(sql, tuple(params))

        logger.info("Pipeline run completed: {run_id} (status={status})", run_id=self.run_id, status=status)
        return self.run_id


def get_latest_run(db: Database) -> dict[str, Any] | None:
    """Fetch the most recent pipeline run record."""
    rows = db.fetchall(
        """
        SELECT id, run_id, started_at, completed_at, status, nima_model_version,
               description_provider, total_files_ingested, total_metrics_scored,
               total_nima_scored, total_described, total_skipped, total_failed,
               notes
        FROM pipeline_runs
        ORDER BY id DESC LIMIT 1
        """
    )
    if not rows:
        return None

    row = rows[0]
    return {
        "id": int(row[0]),
        "run_id": str(row[1]),
        "started_at": row[2],
        "completed_at": row[3],
        "status": str(row[4]) if row[4] else None,
        "nima_model_version": str(row[5]) if row[5] else None,
        "description_provider": str(row[6]) if row[6] else None,
        "total_files_ingested": int(row[7]) if row[7] else 0,
        "total_metrics_scored": int(row[8]) if row[8] else 0,
        "total_nima_scored": int(row[9]) if row[9] else 0,
        "total_described": int(row[10]) if row[10] else 0,
        "total_skipped": int(row[11]) if row[11] else 0,
        "total_failed": int(row[12]) if row[12] else 0,
        "notes": str(row[13]) if row[13] else None,
    }


def get_run_comparison(db: Database, n_runs: int = 5) -> list[dict[str, Any]]:
    """Fetch the last N completed runs for comparison."""
    rows = db.fetchall(
        f"""
        SELECT id, run_id, started_at, completed_at, status, nima_model_version,
               total_files_ingested, total_metrics_scored, total_nima_scored,
               blur_min, blur_max, blur_median, blur_p25, blur_p75, blur_stddev,
               technical_quality_min, technical_quality_max, technical_quality_median,
               technical_quality_p25, technical_quality_p75, technical_quality_stddev,
               nima_min, nima_max, nima_median, nima_p25, nima_p75, nima_stddev,
               aesthetic_min, aesthetic_max, aesthetic_median, aesthetic_p25, aesthetic_p75, aesthetic_stddev,
               curation_min, curation_max, curation_median, curation_p25, curation_p75, curation_stddev,
               semantic_relevance_min, semantic_relevance_max, semantic_relevance_median,
               semantic_relevance_p25, semantic_relevance_p75, semantic_relevance_stddev,
               keep_min, keep_max, keep_median, keep_p25, keep_p75, keep_stddev,
               notes
        FROM pipeline_runs
        WHERE status = 'completed' AND completed_at IS NOT NULL
        ORDER BY id DESC LIMIT {n_runs}
        """
    )

    results = []
    for row in rows:
        results.append({
            "id": int(row[0]),
            "run_id": str(row[1]),
            "started_at": row[2],
            "completed_at": row[3],
            "status": str(row[4]) if row[4] else None,
            "nima_model_version": str(row[5]) if row[5] else None,
            "total_files_ingested": int(row[6]) if row[6] else 0,
            "total_metrics_scored": int(row[7]) if row[7] else 0,
            "total_nima_scored": int(row[8]) if row[8] else 0,
            "blur_min": float(row[9]) if row[9] is not None else None,
            "blur_max": float(row[10]) if row[10] is not None else None,
            "blur_median": float(row[11]) if row[11] is not None else None,
            "blur_p25": float(row[12]) if row[12] is not None else None,
            "blur_p75": float(row[13]) if row[13] is not None else None,
            "blur_stddev": float(row[14]) if row[14] is not None else None,
            "technical_quality_min": float(row[15]) if row[15] is not None else None,
            "technical_quality_max": float(row[16]) if row[16] is not None else None,
            "technical_quality_median": float(row[17]) if row[17] is not None else None,
            "technical_quality_p25": float(row[18]) if row[18] is not None else None,
            "technical_quality_p75": float(row[19]) if row[19] is not None else None,
            "technical_quality_stddev": float(row[20]) if row[20] is not None else None,
            "nima_min": float(row[21]) if row[21] is not None else None,
            "nima_max": float(row[22]) if row[22] is not None else None,
            "nima_median": float(row[23]) if row[23] is not None else None,
            "nima_p25": float(row[24]) if row[24] is not None else None,
            "nima_p75": float(row[25]) if row[25] is not None else None,
            "nima_stddev": float(row[26]) if row[26] is not None else None,
            "aesthetic_min": float(row[27]) if row[27] is not None else None,
            "aesthetic_max": float(row[28]) if row[28] is not None else None,
            "aesthetic_median": float(row[29]) if row[29] is not None else None,
            "aesthetic_p25": float(row[30]) if row[30] is not None else None,
            "aesthetic_p75": float(row[31]) if row[31] is not None else None,
            "aesthetic_stddev": float(row[32]) if row[32] is not None else None,
            "curation_min": float(row[33]) if row[33] is not None else None,
            "curation_max": float(row[34]) if row[34] is not None else None,
            "curation_median": float(row[35]) if row[35] is not None else None,
            "curation_p25": float(row[36]) if row[36] is not None else None,
            "curation_p75": float(row[37]) if row[37] is not None else None,
            "curation_stddev": float(row[38]) if row[38] is not None else None,
            "semantic_relevance_min": float(row[39]) if row[39] is not None else None,
            "semantic_relevance_max": float(row[40]) if row[40] is not None else None,
            "semantic_relevance_median": float(row[41]) if row[41] is not None else None,
            "semantic_relevance_p25": float(row[42]) if row[42] is not None else None,
            "semantic_relevance_p75": float(row[43]) if row[43] is not None else None,
            "semantic_relevance_stddev": float(row[44]) if row[44] is not None else None,
            "keep_min": float(row[45]) if row[45] is not None else None,
            "keep_max": float(row[46]) if row[46] is not None else None,
            "keep_median": float(row[47]) if row[47] is not None else None,
            "keep_p25": float(row[48]) if row[48] is not None else None,
            "keep_p75": float(row[49]) if row[49] is not None else None,
            "keep_stddev": float(row[50]) if row[50] is not None else None,
            "notes": str(row[51]) if row[51] else None,
        })

    return results


def write_run_artifact(
    db: Database,
    run_id: str,
    report_dir: str = "reports",
) -> Path | None:
    """Write a JSON artifact file for the current run to support comparison between runs."""
    stats = get_latest_run(db)
    if not stats:
        return None

    # Get score distributions from DB
    rows = db.fetchall(
        """
        SELECT blur_min, blur_max, blur_median, blur_p25, blur_p75, blur_stddev,
               brightness_min, brightness_max, brightness_median, brightness_p25, brightness_p75, brightness_stddev,
               contrast_min, contrast_max, contrast_median, contrast_p25, contrast_p75, contrast_stddev,
               entropy_min, entropy_max, entropy_median, entropy_p25, entropy_p75, entropy_stddev,
               noise_min, noise_max, noise_median, noise_p25, noise_p75, noise_stddev,
               technical_quality_min, technical_quality_max, technical_quality_median,
               technical_quality_p25, technical_quality_p75, technical_quality_stddev,
               nima_min, nima_max, nima_median, nima_p25, nima_p75, nima_stddev,
               aesthetic_min, aesthetic_max, aesthetic_median, aesthetic_p25, aesthetic_p75, aesthetic_stddev,
               keep_min, keep_max, keep_median, keep_p25, keep_p75, keep_stddev,
               curation_min, curation_max, curation_median, curation_p25, curation_p75, curation_stddev,
               semantic_relevance_min, semantic_relevance_max, semantic_relevance_median,
               semantic_relevance_p25, semantic_relevance_p75, semantic_relevance_stddev
        FROM pipeline_runs WHERE run_id = %s ORDER BY id DESC LIMIT 1
        """,
        (run_id,),
    )

    if not rows:
        return None

    row = rows[0]

    artifact = {
        "run_id": stats["run_id"],
        "started_at": stats["started_at"].isoformat() if stats["started_at"] else None,
        "completed_at": stats["completed_at"].isoformat() if stats["completed_at"] else None,
        "status": stats["status"],
        "nima_model_version": stats["nima_model_version"],
        "description_provider": stats["description_provider"],
        "total_files_ingested": stats["total_files_ingested"],
        "total_metrics_scored": stats["total_metrics_scored"],
        "total_nima_scored": stats["total_nima_scored"],
        "total_described": stats["total_described"],
        "total_skipped": stats["total_skipped"],
        "total_failed": stats["total_failed"],
        "score_distributions": {
            "blur": _row_to_dist(row, 0),
            "brightness": _row_to_dist(row, 6),
            "contrast": _row_to_dist(row, 12),
            "entropy": _row_to_dist(row, 18),
            "noise": _row_to_dist(row, 24),
            "technical_quality": _row_to_dist(row, 30),
            "nima": _row_to_dist(row, 36),
            "aesthetic": _row_to_dist(row, 42),
            "keep": _row_to_dist(row, 48),
            "curation": _row_to_dist(row, 54),
            "semantic_relevance": _row_to_dist(row, 60),
        },
        "notes": stats["notes"],
    }

    artifact_dir = Path(report_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    artifact_path = artifact_dir / f"run_{timestamp}_{run_id[:8]}.json"

    import json
    with artifact_path.open("w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2, default=str)

    logger.info("Run artifact written to {path}", path=str(artifact_path))
    return artifact_path


def _row_to_dist(row: tuple[Any, ...], offset: int) -> dict[str, float | None]:
    """Extract a distribution dict from a DB row starting at the given column offset."""
    vals = [float(v) if v is not None else None for v in row[offset:offset + 6]]
    return {
        "min": vals[0],
        "max": vals[1],
        "median": vals[2],
        "p25": vals[3],
        "p75": vals[4],
        "stddev": vals[5],
    }
