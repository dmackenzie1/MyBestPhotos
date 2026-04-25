from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path
import re
from urllib import error, request

from loguru import logger
from tqdm import tqdm

from photo_curator.db import Database
from photo_curator.pipeline_v1.models import DescriptionOptions, StageStats, is_vision_model
from photo_curator.pipeline_v1.scoring import compute_curation_score

_VISION_MODEL_PATTERNS_STR = ("llava", "moondream", "bakllava", "qwen2.5-vl", "qwen2-vl", "vision")

_CATEGORY_PATTERNS: dict[str, tuple[str, ...]] = {
    "people": (r"\b(person|people|portrait|family|child|children|man|woman|crowd|group)\b",),
    "pets": (r"\b(dog|cat|pet|puppy|kitten|animal)\b",),
    "nature": (r"\b(tree|mountain|beach|lake|forest|sunset|river|sky|waterfall|park)\b",),
    "indoor": (r"\b(indoor|inside|room|kitchen|living room|bedroom|office|home)\b",),
    "outdoor": (r"\b(outdoor|outside|street|yard|garden|trail|field|plaza)\b",),
    "event": (r"\b(wedding|birthday|party|graduation|ceremony|festival|concert|celebration)\b",),
}


def _extract_categories(description_text: str) -> list[str]:
    lowered = description_text.lower()
    detected = [
        category
        for category, patterns in _CATEGORY_PATTERNS.items()
        if any(re.search(pattern, lowered) for pattern in patterns)
    ]
    return sorted(detected)


def _describe_with_lmstudio(
    path: Path,
    filename: str,
    camera_make: str | None,
    camera_model: str | None,
    options: DescriptionOptions,
) -> str | None:
    mime_type = mimetypes.guess_type(filename)[0] or "image/jpeg"
    image_base64 = base64.b64encode(path.read_bytes()).decode("utf-8")

    prompt = (
        "Describe this personal photo in 1-2 neutral sentences suitable for search. "
        "Mention obvious subjects, scene context, and photographic qualities if clear. "
        "Avoid guessing names or sensitive details."
    )
    if camera_make or camera_model:
        prompt += f" Camera metadata: {camera_make or 'unknown'} {camera_model or 'unknown'}."

    payload = {
        "model": options.lmstudio_model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_base64}",
                        },
                    },
                ],
            }
        ],
        "temperature": 0.1,
    }
    body = json.dumps(payload).encode("utf-8")
    if not is_vision_model(options.lmstudio_model):
        logger.warning(
            "Model '{model}' does not appear to be vision-capable (patterns: {patterns}). "
            "Vision payloads will likely be rejected by LM Studio with HTTP 400. "
            "Load a model like qwen2.5-vl-7b-instruct or llava for image support.",
            model=options.lmstudio_model,
            patterns=_VISION_MODEL_PATTERNS_STR,
        )

    endpoint = f"{options.lmstudio_base_url.rstrip('/')}/chat/completions"
    req = request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=options.lmstudio_timeout_seconds) as response:
            response_body = response.read()
    except (TimeoutError, error.URLError, error.HTTPError) as exc:
        if isinstance(exc, error.HTTPError):
            body = None
            try:
                body = exc.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            logger.warning(
                "LM Studio request failed for {path}: HTTP {code} {reason}: {body}",
                path=path,
                code=exc.code,
                reason=exc.reason,
                body=body or "(no body)",
            )
        else:
            logger.warning("LM Studio request failed for {path}: {error}", path=path, error=exc)
        return None

    try:
        parsed = json.loads(response_body.decode("utf-8"))
        content = parsed["choices"][0]["message"]["content"]
    except (KeyError, IndexError, json.JSONDecodeError, TypeError) as exc:
        logger.warning("LM Studio response parse failed for {path}: {error}", path=path, error=exc)
        return None

    if not isinstance(content, str):
        return None
    cleaned = content.strip()
    return cleaned or None


def describe_images(
    db: Database,
    model_name: str = "basic-caption-v1",
    options: DescriptionOptions | None = None,
) -> StageStats:
    resolved_options = options or DescriptionOptions()
    if resolved_options.provider not in {"basic", "lmstudio"}:
        logger.warning(
            "Unknown description provider '{provider}', falling back to basic",
            provider=resolved_options.provider,
        )
        resolved_options = DescriptionOptions(
            provider="basic",
            lmstudio_base_url=resolved_options.lmstudio_base_url,
            lmstudio_model=resolved_options.lmstudio_model,
            lmstudio_timeout_seconds=resolved_options.lmstudio_timeout_seconds,
        )
    rows = db.fetchall(
        """
        SELECT f.id, f.filename, f.source_root, f.relative_path, f.camera_make, f.camera_model, f.photo_taken_at,
               m.blur_score, m.brightness_score, m.contrast_score,
               m.technical_quality_score, m.aesthetic_score, m.keep_score
        FROM files f
        LEFT JOIN file_metrics m ON m.file_id = f.id
        ORDER BY f.id
        """
    )

    stats = StageStats()
    for row in tqdm(rows, desc="Descriptions"):
        (
            file_id,
            filename,
            source_root,
            relative_path,
            camera_make,
            camera_model,
            photo_taken_at,
            blur_score,
            brightness_score,
            contrast_score,
            technical_quality_score,
            aesthetic_score,
            keep_score,
        ) = row

        quality_hint = "good"
        if technical_quality_score is not None:
            if technical_quality_score >= 0.8:
                quality_hint = "excellent"
            elif technical_quality_score < 0.5:
                quality_hint = "fair"

        basic_description_text = (
            f"Photo {filename} captured"
            + (f" on {photo_taken_at.date()}" if photo_taken_at else "")
            + (f" with {camera_make} {camera_model}" if camera_make or camera_model else "")
            + f". Overall technical quality looks {quality_hint}."
        )
        description_text = basic_description_text
        if resolved_options.provider == "lmstudio":
            photo_path = Path(source_root) / relative_path
            if photo_path.exists():
                lmstudio_description = _describe_with_lmstudio(
                    photo_path,
                    filename=filename,
                    camera_make=camera_make,
                    camera_model=camera_model,
                    options=resolved_options,
                )
                if lmstudio_description:
                    description_text = lmstudio_description
            else:
                logger.warning(
                    "Source file not found for description, skipping LM Studio: file_id={id} path={path}",
                    id=file_id,
                    path=photo_path,
                )

        semantic_relevance_score = 0.0
        categories = _extract_categories(description_text)

        # Description richness: unique word ratio and length contribute to content quality
        if description_text:
            words = description_text.split()
            unique_words = len(set(w.lower() for w in words))
            total_words = max(len(words), 1)
            unique_ratio = unique_words / total_words

            # Length component: longer descriptions tend to be more descriptive
            length_score = min(1.0, total_words / 30.0)

            # Unique word ratio bonus: diverse vocabulary indicates richer content
            vocab_bonus = unique_ratio * 0.25

            semantic_relevance_score += length_score * 0.4 + vocab_bonus

        # Category richness: primary differentiator with basic descriptions
        if categories:
            category_bonus = min(1.0, len(categories) / 3.0) ** 0.8 * 0.45
            semantic_relevance_score += category_bonus

        # Technical quality as a proxy for "describability": sharper photos are more relevant
        if technical_quality_score is not None and technical_quality_score > 0:
            tech_bonus = (technical_quality_score - 0.3) * 0.25
            semantic_relevance_score += max(0, min(tech_bonus, 0.15))

        # Clamp to [0, 1]
        semantic_relevance_score = max(0.0, min(1.0, semantic_relevance_score))

        _aesthetic = aesthetic_score if aesthetic_score is not None else 0.5
        _keep = keep_score if keep_score is not None else 0.5
        _tech = technical_quality_score if technical_quality_score is not None else 0.0
        curation_score = compute_curation_score(_aesthetic, _keep, _tech, semantic_relevance_score)

        try:
            db.execute(
                """
                UPDATE file_metrics
                SET semantic_relevance_score = %s,
                    curation_score = %s,
                    updated_at = now()
                WHERE file_id = %s
                """,
                (semantic_relevance_score, curation_score, file_id),
            )
        except Exception as exc:
            logger.warning(
                "Could not update semantic/curation score for file_id={id}: {error}",
                id=file_id,
                error=str(exc),
            )

        description_json = {
            "provider": resolved_options.provider,
            "quality_hint": quality_hint,
            "camera_make": camera_make,
            "camera_model": camera_model,
            "scores": {
                "technical_quality": technical_quality_score,
                "semantic_relevance": semantic_relevance_score,
                "curation": curation_score,
                "blur": blur_score,
                "brightness": brightness_score,
                "contrast": contrast_score,
            },
            "categories": categories,
        }

        try:
            db.execute(
                """
                INSERT INTO file_descriptions (file_id, model_name, description_text, description_json)
                VALUES (%s, %s, %s, %s::jsonb)
                ON CONFLICT (file_id) DO UPDATE SET
                  model_name = EXCLUDED.model_name,
                  description_text = EXCLUDED.description_text,
                  description_json = EXCLUDED.description_json,
                  updated_at = now()
                """,
                (file_id, model_name, description_text, json.dumps(description_json)),
            )
            stats.processed += 1
        except Exception as exc:
            logger.error(
                "Description DB insert failed for file_id={id}: {error}", id=file_id, error=str(exc)
            )

    logger.info(
        "Description stage complete: processed={count}, provider={provider}",
        count=stats.processed,
        provider=resolved_options.provider,
    )
    return stats
