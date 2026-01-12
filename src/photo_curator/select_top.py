from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

import numpy as np
from loguru import logger

from photo_curator.config import Settings
from photo_curator.db import Database


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
    rows = db.fetchall(
        """
        SELECT p.id, m.sharpness, m.contrast, m.exposure_clip_hi, m.aesthetic_score, e.embedding
        FROM photos p
        LEFT JOIN metrics m ON m.photo_id = p.id
        JOIN embeddings e ON e.photo_id = p.id AND e.model_name = %s
        """,
        (settings.clip_model,),
    )

    candidates = []
    for photo_id, sharpness, contrast, clip_hi, aesthetic, embedding in rows:
        score = _combined_score(sharpness, contrast, clip_hi, aesthetic, settings)
        candidates.append((photo_id, score, np.array(embedding, dtype=np.float32)))

    candidates.sort(key=lambda row: row[1], reverse=True)
    selected: list[tuple[int, float, np.ndarray]] = []

    for photo_id, score, vec in candidates:
        penalty = 0.0
        for _, _, sel_vec in selected:
            sim = _cosine(vec, sel_vec)
            if sim > settings.similarity_threshold:
                penalty = max(penalty, settings.lambda_penalty * sim)
        final = score - penalty
        if len(selected) < top_n:
            selected.append((photo_id, final, vec))
        else:
            lowest_idx = min(range(len(selected)), key=lambda i: selected[i][1])
            if final > selected[lowest_idx][1]:
                selected[lowest_idx] = (photo_id, final, vec)

    selected.sort(key=lambda row: row[1], reverse=True)
    with db.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO runs (started_at) VALUES (%s) RETURNING id", (datetime.now(timezone.utc),))
            run_id = cur.fetchone()[0]
            for rank, (photo_id, final_score, _) in enumerate(selected, start=1):
                cur.execute(
                    """
                    INSERT INTO selections (run_id, photo_id, rank, final_score)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (run_id, photo_id, rank, final_score),
                )
            cur.execute("UPDATE runs SET finished_at = %s WHERE id = %s", (datetime.now(timezone.utc), run_id))
            conn.commit()

    logger.info("Selection complete: run_id={run_id}, total={count}", run_id=run_id, count=len(selected))
    return SelectionResult(run_id=run_id, selected=[(pid, score) for pid, score, _ in selected])
