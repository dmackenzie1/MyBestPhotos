from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from loguru import logger
import numpy as np
from PIL import Image
from tqdm import tqdm

import torch
import open_clip
from pgvector.psycopg import register_vector

from photo_curator.config import Settings
from photo_curator.db import Database
from photo_curator.utils.hashing import sha256_file


@dataclass
class EmbeddingStats:
    processed: int = 0
    fallback_used: bool = False


def _device_from_setting(setting: str) -> str:
    if setting == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return setting


def _fallback_embedding(path: Path, dim: int = 512) -> list[float]:
    digest = sha256_file(path)
    bits = [int(bit, 16) for bit in digest]
    vector = np.array(bits * (dim // len(bits) + 1))[:dim].astype(np.float32)
    vector = (vector - vector.mean()) / (vector.std() + 1e-6)
    return vector.tolist()


def _iter_batches(items: list[tuple[int, str]], batch_size: int) -> Iterable[list[tuple[int, str]]]:
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]


def embed(
    db: Database,
    settings: Settings,
    model_name: str,
    weights_path: str | None,
    batch_size: int,
    device: str,
    force: bool = False,
) -> EmbeddingStats:
    photos = db.fetchall(
        """
        SELECT id, path FROM photos
        WHERE (%s) OR (id NOT IN (SELECT photo_id FROM embeddings WHERE model_name = %s))
        """,
        (force, model_name),
    )

    stats = EmbeddingStats()
    if not photos:
        return stats

    weights = Path(weights_path) if weights_path else None
    use_fallback = weights is None or not weights.exists()

    if use_fallback:
        logger.warning("CLIP weights not found. Using deterministic fallback embeddings.")
        stats.fallback_used = True

    if not use_fallback:
        device = _device_from_setting(device)
        model, _, preprocess = open_clip.create_model_and_transforms(
            model_name,
            pretrained=None,
        )
        state = torch.load(weights, map_location="cpu")
        model.load_state_dict(state)
        model.to(device)
        model.eval()
        dim = model.visual.output_dim
    else:
        preprocess = None
        dim = 512

    with db.connection() as conn:
        register_vector(conn)

    for batch in tqdm(_iter_batches(photos, batch_size), desc="Embedding", total=len(photos) // batch_size + 1):
        if use_fallback:
            embeddings = [(_fallback_embedding(Path(path), dim=dim), photo_id) for photo_id, path in batch]
        else:
            images = []
            ids = []
            for photo_id, path in batch:
                image = Image.open(path).convert("RGB")
                images.append(preprocess(image))
                ids.append(photo_id)
            image_tensor = torch.stack(images).to(device)
            with torch.no_grad():
                emb = model.encode_image(image_tensor)
                emb = emb / emb.norm(dim=-1, keepdim=True)
                embeddings = [(emb[i].cpu().numpy().tolist(), ids[i]) for i in range(len(ids))]

        for vector, photo_id in embeddings:
            db.execute(
                """
                INSERT INTO embeddings (photo_id, model_name, embedding)
                VALUES (%s, %s, %s)
                ON CONFLICT (photo_id, model_name) DO UPDATE SET
                    embedding = EXCLUDED.embedding,
                    created_at = now()
                """,
                (photo_id, model_name, vector),
            )
            stats.processed += 1

    logger.info("Embedding complete: processed={processed}", processed=stats.processed)
    return stats
