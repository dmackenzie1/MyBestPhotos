from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from loguru import logger
import numpy as np
from tqdm import tqdm

import torch
import open_clip

from photo_curator.db import Database


@dataclass
class AestheticStats:
    processed: int = 0
    fallback_used: bool = False


POSITIVE_PROMPTS = [
    "a beautiful photo",
    "a well composed photograph",
    "a sharp professional photo",
]
NEGATIVE_PROMPTS = [
    "a blurry photo",
    "an overexposed photo",
    "a poorly composed snapshot",
]


def _device_from_setting(setting: str) -> str:
    if setting == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return setting


def _sigmoid(value: float) -> float:
    return float(1 / (1 + np.exp(-value)))


def _heuristic_score(sharpness: float | None, contrast: float | None, clip_hi: float | None) -> float:
    sharp = min((sharpness or 0.0) / 500.0, 1.0)
    contrast_score = min((contrast or 0.0) * 2.0, 1.0)
    clip_penalty = min((clip_hi or 0.0) * 5.0, 1.0)
    score = (sharp * 0.5 + contrast_score * 0.5) * (1.0 - clip_penalty)
    return float(np.clip(score, 0.0, 1.0))


def score_aesthetic(
    db: Database,
    model_name: str,
    weights_path: str | None,
    device: str,
) -> AestheticStats:
    rows = db.fetchall(
        """
        SELECT p.id, e.embedding, m.sharpness, m.contrast, m.exposure_clip_hi
        FROM photos p
        JOIN embeddings e ON e.photo_id = p.id AND e.model_name = %s
        LEFT JOIN metrics m ON m.photo_id = p.id
        """,
        (model_name,),
    )

    stats = AestheticStats()
    if not rows:
        return stats

    weights = Path(weights_path) if weights_path else None
    use_fallback = weights is None or not weights.exists()

    if use_fallback:
        logger.warning("CLIP weights not found. Using heuristic aesthetic scoring.")
        stats.fallback_used = True
        for photo_id, _, sharpness, contrast, clip_hi in tqdm(rows, desc="Aesthetic scoring"):
            score = _heuristic_score(sharpness, contrast, clip_hi)
            db.execute(
                """
                INSERT INTO metrics (photo_id, aesthetic_score)
                VALUES (%s, %s)
                ON CONFLICT (photo_id) DO UPDATE SET
                    aesthetic_score = EXCLUDED.aesthetic_score
                """,
                (photo_id, score),
            )
            stats.processed += 1
        return stats

    device = _device_from_setting(device)
    model, _, _ = open_clip.create_model_and_transforms(model_name, pretrained=None)
    state = torch.load(weights, map_location="cpu")
    model.load_state_dict(state)
    model.to(device)
    model.eval()

    tokenizer = open_clip.get_tokenizer(model_name)
    with torch.no_grad():
        pos_tokens = tokenizer(POSITIVE_PROMPTS).to(device)
        neg_tokens = tokenizer(NEGATIVE_PROMPTS).to(device)
        pos_emb = model.encode_text(pos_tokens)
        neg_emb = model.encode_text(neg_tokens)
        pos_emb = pos_emb / pos_emb.norm(dim=-1, keepdim=True)
        neg_emb = neg_emb / neg_emb.norm(dim=-1, keepdim=True)
        pos_mean = pos_emb.mean(dim=0)
        neg_mean = neg_emb.mean(dim=0)

    for photo_id, embedding, *_ in tqdm(rows, desc="Aesthetic scoring"):
        image_vec = np.array(embedding, dtype=np.float32)
        image_vec = image_vec / (np.linalg.norm(image_vec) + 1e-6)
        pos_sim = float(np.dot(image_vec, pos_mean.cpu().numpy()))
        neg_sim = float(np.dot(image_vec, neg_mean.cpu().numpy()))
        score = _sigmoid(pos_sim - neg_sim)
        db.execute(
            """
            INSERT INTO metrics (photo_id, aesthetic_score)
            VALUES (%s, %s)
            ON CONFLICT (photo_id) DO UPDATE SET
                aesthetic_score = EXCLUDED.aesthetic_score
            """,
            (photo_id, score),
        )
        stats.processed += 1

    logger.info("Aesthetic scoring complete: processed={processed}", processed=stats.processed)
    return stats
