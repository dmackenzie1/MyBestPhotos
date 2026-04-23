from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from loguru import logger
import numpy as np
from PIL import Image
from tqdm import tqdm

import open_clip
import torch

from photo_curator.db import Database
from photo_curator.pipeline_run import _compute_distribution


@dataclass
class AestheticStats:
    processed: int = 0
    failed: int = 0


@dataclass
class ClipAestheticScorer:
    model: torch.nn.Module
    preprocess: Callable[[Image.Image], torch.Tensor]
    pos_mean: torch.Tensor
    neg_mean: torch.Tensor
    device: str

    def score_pil_images(self, images: list[Image.Image]) -> list[float]:
        if not images:
            return []
        image_tensors = [self.preprocess(image.convert("RGB")) for image in images]
        image_tensor = torch.stack(image_tensors).to(self.device)
        with torch.no_grad():
            image_emb = self.model.encode_image(image_tensor)
            image_emb = image_emb / image_emb.norm(dim=-1, keepdim=True)
            pos_scores = image_emb @ self.pos_mean
            neg_scores = image_emb @ self.neg_mean
        return [
            _sigmoid(float(pos_scores[i].item() - neg_scores[i].item())) for i in range(len(images))
        ]


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


def _iter_batches(items: list[tuple[Any, ...]], batch_size: int) -> Iterable[list[tuple[Any, ...]]]:
    for idx in range(0, len(items), batch_size):
        yield items[idx : idx + batch_size]


def _resolve_clip(model_name: str, device: str) -> ClipAestheticScorer:
    resolved_device = _device_from_setting(device)
    available_pretrained = [tag for arch, tag in open_clip.list_pretrained() if arch == model_name]
    pretrained_tag = "openai" if "openai" in available_pretrained else None
    if pretrained_tag is None and available_pretrained:
        pretrained_tag = available_pretrained[0]

    if pretrained_tag:
        logger.info(
            "Loading CLIP model with pretrained weights: model={model} pretrained={pretrained}",
            model=model_name,
            pretrained=pretrained_tag,
        )
        try:
            model, _, preprocess = open_clip.create_model_and_transforms(
                model_name, pretrained=pretrained_tag
            )
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "Failed to load CLIP pretrained weights. "
                "Verify network/proxy access to Hugging Face or pre-populate the model cache."
            ) from exc
    else:
        logger.warning(
            "No pretrained weights published for model={model}; CLIP will run with random init",
            model=model_name,
        )
        model, _, preprocess = open_clip.create_model_and_transforms(model_name, pretrained=None)

    model.to(resolved_device)
    model.eval()

    tokenizer = open_clip.get_tokenizer(model_name)
    with torch.no_grad():
        pos_tokens = tokenizer(POSITIVE_PROMPTS).to(resolved_device)
        neg_tokens = tokenizer(NEGATIVE_PROMPTS).to(resolved_device)
        pos_emb = model.encode_text(pos_tokens)
        neg_emb = model.encode_text(neg_tokens)
        pos_emb = pos_emb / pos_emb.norm(dim=-1, keepdim=True)
        neg_emb = neg_emb / neg_emb.norm(dim=-1, keepdim=True)

    return ClipAestheticScorer(
        model=model,
        preprocess=preprocess,
        pos_mean=pos_emb.mean(dim=0),
        neg_mean=neg_emb.mean(dim=0),
        device=resolved_device,
    )


def load_clip_aesthetic_scorer(model_name: str, device: str) -> ClipAestheticScorer:
    return _resolve_clip(model_name, device)


def score_aesthetic(
    db: Database,
    model_name: str,
    weights_path: str | None,
    device: str,
) -> AestheticStats:
    """Legacy photos/metrics scoring entrypoint; kept for backwards compatibility."""
    if weights_path:
        logger.info(
            "Ignoring explicit weights_path for aesthetics; open_clip auto-download is used."
        )

    rows = db.fetchall(
        """
        SELECT p.id, p.path
        FROM photos p
        LEFT JOIN metrics m ON m.photo_id = p.id
        WHERE m.aesthetic_score IS NULL
        ORDER BY p.id ASC
        """
    )

    stats = AestheticStats()
    if not rows:
        return stats

    scorer = _resolve_clip(model_name, device)

    for batch in tqdm(_iter_batches(rows, batch_size=32), desc="Aesthetic scoring (legacy)"):
        images: list[torch.Tensor] = []
        ids: list[int] = []
        for photo_id, path in batch:
            try:
                with Image.open(path) as image:
                    images.append(image.copy())
                    ids.append(int(photo_id))
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to read image for CLIP scoring: {path} ({error})", path=path, error=exc
                )
                stats.failed += 1

        if not images:
            continue

        scores = scorer.score_pil_images(images)
        for photo_id, aesthetic in zip(ids, scores, strict=False):
            db.execute(
                """
                INSERT INTO metrics (photo_id, aesthetic_score)
                VALUES (%s, %s)
                ON CONFLICT (photo_id) DO UPDATE SET
                    aesthetic_score = EXCLUDED.aesthetic_score
                """,
                (photo_id, aesthetic),
            )
            stats.processed += 1

    logger.info(
        "Legacy aesthetic scoring complete: processed={processed} failed={failed}",
        processed=stats.processed,
        failed=stats.failed,
    )
    return stats


def score_file_aesthetic(
    db: Database,
    model_name: str,
    device: str,
    *,
    batch_size: int = 32,
    only_missing: bool = True,
) -> AestheticStats:
    predicate = "fm.aesthetic_score IS NULL" if only_missing else "TRUE"
    rows = db.fetchall(
        f"""
        SELECT f.id, f.source_root, f.relative_path
        FROM files f
        LEFT JOIN file_metrics fm ON fm.file_id = f.id
        WHERE {predicate}
        ORDER BY f.id ASC
        """
    )

    stats = AestheticStats()
    if not rows:
        return stats

    scorer = _resolve_clip(model_name, device)

    scored_values: list[float] = []
    for batch in tqdm(_iter_batches(rows, batch_size=batch_size), desc="Aesthetic scoring"):
        images: list[torch.Tensor] = []
        ids: list[int] = []

        for file_id, source_root, relative_path in batch:
            path = Path(source_root) / Path(relative_path)
            try:
                with Image.open(path) as image:
                    images.append(image.copy())
                    ids.append(int(file_id))
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to read image for CLIP scoring: {path} ({error})",
                    path=path,
                    error=exc,
                )
                stats.failed += 1

        if not images:
            continue

        scores = scorer.score_pil_images(images)
        for file_id, aesthetic in zip(ids, scores, strict=False):
            db.execute(
                """
                INSERT INTO file_metrics (file_id, aesthetic_score, advanced_metadata_updated_at)
                VALUES (%s, %s, now())
                ON CONFLICT (file_id) DO UPDATE SET
                  aesthetic_score = EXCLUDED.aesthetic_score,
                  advanced_metadata_updated_at = now(),
                  updated_at = now()
                """,
                (file_id, aesthetic),
            )
            scored_values.append(aesthetic)
            stats.processed += 1

    if scored_values:
        dist = _compute_distribution(scored_values)
        logger.info(
            "CLIP aesthetic distribution: n={count} min={min_val:.4f} p25={p25:.4f} median={median:.4f} p75={p75:.4f} p90={p90:.4f} max={max_val:.4f} stddev={stddev:.4f}",
            count=dist.count,
            min_val=dist.min_val,
            p25=dist.p25,
            median=dist.median,
            p75=dist.p75,
            p90=dist.p90,
            max_val=dist.max_val,
            stddev=dist.stddev,
        )

    logger.info(
        "CLIP aesthetic scoring complete: processed={processed} failed={failed}",
        processed=stats.processed,
        failed=stats.failed,
    )
    return stats
