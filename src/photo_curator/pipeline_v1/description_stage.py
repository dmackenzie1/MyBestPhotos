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
from photo_curator.pipeline_v1.models import DescriptionOptions, StageStats

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
               m.print_score_12x18, m.blur_score, m.brightness_score, m.contrast_score,
               m.technical_quality_score, m.keep_score
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
            print_12x18,
            blur_score,
            brightness_score,
            contrast_score,
            technical_quality_score,
            keep_score,
        ) = row

        quality_hint = "good"
        if print_12x18 is not None:
            if print_12x18 >= 0.85:
                quality_hint = "excellent"
            elif print_12x18 < 0.6:
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

        semantic_relevance_score = 0.15
        categories = _extract_categories(description_text)
        if description_text:
            semantic_relevance_score += min(0.45, len(description_text.split()) / 40.0)
        if camera_make or camera_model:
            semantic_relevance_score += 0.1
        semantic_relevance_score += min(0.25, 0.08 * len(categories))
        semantic_relevance_score = max(0.0, min(1.0, semantic_relevance_score))

        ranking_quality_score = (
            keep_score
            if keep_score is not None
            else (technical_quality_score or print_12x18 or 0.0)
        )
        curation_score = max(
            0.0,
            min(
                1.0,
                (0.7 * ranking_quality_score) + (0.3 * semantic_relevance_score),
            ),
        )

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
                "print_12x18": print_12x18,
                "technical_quality": technical_quality_score,
                "keep_score": keep_score,
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
