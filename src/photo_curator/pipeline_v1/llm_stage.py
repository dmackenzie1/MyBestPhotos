from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path
from urllib import error, request

from loguru import logger
from tqdm import tqdm

from photo_curator.db import Database
from photo_curator.pipeline_v1.models import DescriptionOptions, StageStats, is_vision_model
from photo_curator.text_vectorizer import embed_text, vector_literal

PROMPT_VERSION = "llm_photo_v1"
EMBEDDING_MODEL = "hash-embed-v1"

_VISION_MODEL_PATTERNS_STR = ("llava", "moondream", "bakllava", "qwen2.5-vl", "qwen2-vl", "vision")


def _safe_float(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return max(0.0, min(100.0, float(value)))
    if isinstance(value, str):
        stripped = value.strip()
        try:
            parsed = float(stripped)
        except ValueError:
            return None
        return max(0.0, min(100.0, parsed))
    return None


def _call_lmstudio(path: Path, options: DescriptionOptions) -> dict[str, object] | None:
    mime_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    image_base64 = base64.b64encode(path.read_bytes()).decode("utf-8")
    prompt = (
        "Return strict JSON only with shape: "
        '{"description":"one-paragraph neutral description",'
        '"tags":["tag1","tag2"],'
        '"aesthetic_score":0-100,'
        '"wall_art_score":0-100}. '
        "Keep tags short lowercase nouns/adjectives and avoid names/PII."
    )
    payload = {
        "model": options.lmstudio_model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{image_base64}"},
                    },
                ],
            }
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }
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
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=options.lmstudio_timeout_seconds) as response:
            raw = json.loads(response.read().decode("utf-8"))
        content = raw["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            return None
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
    except (
        TimeoutError,
        error.URLError,
        error.HTTPError,
        KeyError,
        IndexError,
        json.JSONDecodeError,
    ) as exc:
        if isinstance(exc, error.HTTPError):
            body = None
            try:
                body = exc.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            logger.warning(
                "LLM call failed for {path}: HTTP {code} {reason}: {body}",
                path=path,
                code=exc.code,
                reason=exc.reason,
                body=body or "(no body)",
            )
        else:
            logger.warning("LLM call failed for {path}: {error}", path=path, error=exc)
    return None


def run_llm_descriptions(
    db: Database,
    *,
    options: DescriptionOptions,
    prompt_version: str = PROMPT_VERSION,
    embedding_model: str = EMBEDDING_MODEL,
) -> StageStats:
    run_row = db.fetchall(
        """
        INSERT INTO llm_runs (provider, endpoint, vision_model_name, embedding_model_name, prompt_version, prompt_text)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            "lmstudio",
            options.lmstudio_base_url,
            options.lmstudio_model,
            embedding_model,
            prompt_version,
            "photo description + tags + scores JSON",
        ),
    )
    run_id = int(run_row[0][0]) if run_row else None

    rows = db.fetchall(
        """
        SELECT id, source_root, relative_path
        FROM files
        ORDER BY id
        """
    )
    stats = StageStats()
    for file_id, source_root, relative_path in tqdm(rows, desc="LLM descriptions"):
        path = Path(source_root) / str(relative_path)
        if not path.exists():
            logger.warning(
                "Skipping missing source file for LLM: file_id={file_id} path={path}",
                file_id=file_id,
                path=path,
            )
            continue
        response = _call_lmstudio(path, options)
        if not response:
            continue

        description = str(response.get("description", "")).strip()
        tags_raw = response.get("tags", [])
        tags = [
            str(tag).strip().lower()
            for tag in tags_raw
            if isinstance(tag, str) and str(tag).strip()
        ]
        aesthetic_score = _safe_float(response.get("aesthetic_score"))
        wall_art_score = _safe_float(response.get("wall_art_score"))
        if not description:
            continue
        embedding = embed_text(f"{description} {' '.join(tags)}")
        payload_json = {
            "description": description,
            "tags": tags,
            "aesthetic_score": aesthetic_score,
            "wall_art_score": wall_art_score,
            "prompt_version": prompt_version,
            "vision_model_name": options.lmstudio_model,
            "embedding_model_name": embedding_model,
        }
        db.execute(
            """
            INSERT INTO file_llm_results (
              file_id, llm_run_id, prompt_version, vision_model_name, embedding_model_name,
              description_text, tags, llm_payload_json, aesthetic_score, wall_art_score, description_embedding, processed_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s::vector, now())
            ON CONFLICT (file_id) DO UPDATE SET
              llm_run_id = EXCLUDED.llm_run_id,
              prompt_version = EXCLUDED.prompt_version,
              vision_model_name = EXCLUDED.vision_model_name,
              embedding_model_name = EXCLUDED.embedding_model_name,
              description_text = EXCLUDED.description_text,
              tags = EXCLUDED.tags,
              llm_payload_json = EXCLUDED.llm_payload_json,
              aesthetic_score = EXCLUDED.aesthetic_score,
              wall_art_score = EXCLUDED.wall_art_score,
              description_embedding = EXCLUDED.description_embedding,
              processed_at = EXCLUDED.processed_at,
              updated_at = now()
            """,
            (
                file_id,
                run_id,
                prompt_version,
                options.lmstudio_model,
                embedding_model,
                description,
                tags,
                json.dumps(payload_json),
                aesthetic_score,
                wall_art_score,
                vector_literal(embedding),
            ),
        )
        stats.processed += 1

    logger.info(
        "LLM stage complete: processed={count} run_id={run_id}",
        count=stats.processed,
        run_id=run_id,
    )
    return stats
