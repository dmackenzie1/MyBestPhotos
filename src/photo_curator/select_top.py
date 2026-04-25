from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import numpy as np
from loguru import logger

from photo_curator.config import Settings
from photo_curator.db import Database


def _existing_tables(db: Database, table_names: set[str]) -> set[str]:
    rows = db.fetchall(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = ANY(%s)
        """,
        (list(table_names),),
    )
    return {str(row[0]) for row in rows}


def _selection_mode(db: Database) -> str:
    legacy_required = {"photos", "metrics", "embeddings", "runs", "selections"}
    v1_required = {"files", "file_metrics"}
    existing = _existing_tables(db, legacy_required | v1_required)
    if legacy_required.issubset(existing):
        return "legacy"
    if v1_required.issubset(existing):
        return "v1"
    missing = sorted(v1_required - existing)
    raise RuntimeError(
        "Selection pipeline requires either legacy tables "
        "(photos/metrics/embeddings/runs/selections) or v1 tables (files/file_metrics). "
        f"Missing v1 tables: {', '.join(missing)}."
    )


def _as_vector(value: object) -> np.ndarray | None:
    if value is None:
        return None
    try:
        vec = np.array(value, dtype=np.float32)
    except (TypeError, ValueError):
        return None
    if vec.size == 0:
        return None
    return vec


def _legacy_rows(
    db: Database, settings: Settings
) -> list[tuple[int, float | None, float | None, float | None, float | None, object]]:
    return db.fetchall(
        """
        SELECT p.id, m.sharpness, m.contrast, m.exposure_clip_hi, m.aesthetic_score, e.embedding
        FROM photos p
        LEFT JOIN metrics m ON m.photo_id = p.id
        JOIN embeddings e ON e.photo_id = p.id AND e.model_name = %s
        """,
        (settings.clip_model,),
    )


def _v1_rows(
    db: Database, settings: Settings
) -> list[tuple[int, float | None, float | None, float | None, float | None, object]]:
    return db.fetchall(
        """
        SELECT
          f.id,
          fm.blur_score,
          fm.contrast_score,
          NULL::double precision AS exposure_clip_hi,
           COALESCE(fm.aesthetic_score, fm.clip_aesthetic_score) AS aesthetic_score,
          flr.description_embedding
        FROM files f
        LEFT JOIN file_metrics fm ON fm.file_id = f.id
        LEFT JOIN file_llm_results flr
          ON flr.file_id = f.id
          AND flr.embedding_model_name = %s
        """,
        ("hash-embed-v1",),
    )


@dataclass
class SelectionResult:
    run_id: int
    selected: list[tuple[int, float]]


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / ((np.linalg.norm(a) + 1e-6) * (np.linalg.norm(b) + 1e-6)))


def _combined_score(
    sharpness: float | None,
    contrast: float | None,
    clip_hi: float | None,
    aesthetic: float | None,
    settings: Settings,
) -> float:
    tech_score = (sharpness or 0.0) * 0.001 + (contrast or 0.0) - (clip_hi or 0.0)
    tech_score = float(np.clip(tech_score, 0.0, 1.0))
    aesthetic_score = aesthetic or 0.0
    return settings.weights_technical * tech_score + settings.weights_aesthetic * aesthetic_score


def select_top(
    db: Database,
    settings: Settings,
    top_n: int,
) -> SelectionResult:
    mode = _selection_mode(db)
    rows = _legacy_rows(db, settings) if mode == "legacy" else _v1_rows(db, settings)

    candidates: list[tuple[int, float, np.ndarray | None]] = []
    for photo_id, sharpness, contrast, clip_hi, aesthetic, embedding in rows:
        score = _combined_score(sharpness, contrast, clip_hi, aesthetic, settings)
        candidates.append((photo_id, score, _as_vector(embedding)))

    candidates.sort(key=lambda row: row[1], reverse=True)
    selected: list[tuple[int, float, np.ndarray | None]] = []

    for photo_id, score, vec in candidates:
        penalty = 0.0
        for _, _, sel_vec in selected:
            if vec is None or sel_vec is None:
                continue
            sim = _cosine(vec, sel_vec)
            if sim > settings.similarity_threshold:
                penalty = max(penalty, settings.lambda_penalty * sim)
        final = score - penalty
        if len(selected) < top_n:
            selected.append((photo_id, final, vec))
        else:
            lowest_idx, _lowest = min(enumerate(selected), key=lambda row: row[1][1])
            if final > selected[lowest_idx][1]:
                selected[lowest_idx] = (photo_id, final, vec)

    selected.sort(key=lambda row: row[1], reverse=True)
    if mode == "legacy":
        with db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO runs (started_at) VALUES (%s) RETURNING id",
                    (datetime.now(timezone.utc),),
                )
                run_id = cur.fetchone()[0]
                for rank, (photo_id, final_score, _) in enumerate(selected, start=1):
                    cur.execute(
                        """
                        INSERT INTO selections (run_id, photo_id, rank, final_score)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (run_id, photo_id, rank, final_score),
                    )
                cur.execute(
                    "UPDATE runs SET finished_at = %s WHERE id = %s",
                    (datetime.now(timezone.utc), run_id),
                )
                conn.commit()
    else:
        run_id = 0
        logger.info(
            "Selection ran in v1 compatibility mode (files/file_metrics). "
            "Results are returned but not persisted to legacy runs/selections tables."
        )

    logger.info(
        "Selection complete: mode={mode} run_id={run_id} total={count}",
        mode=mode,
        run_id=run_id,
        count=len(selected),
    )
    return SelectionResult(run_id=run_id, selected=[(pid, score) for pid, score, _ in selected])
