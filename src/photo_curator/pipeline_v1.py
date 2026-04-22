from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import base64
import random
import json
import mimetypes
from pathlib import Path
import re
from typing import Iterable
from urllib import error, request

import cv2
from loguru import logger
import numpy as np
from tqdm import tqdm

from photo_curator.config import Settings
from photo_curator.db import Database
from photo_curator.utils.hashing import sha256_file
from photo_curator.utils.image import SUPPORTED_EXTENSIONS, get_exif, open_image

DATE_RE = re.compile(r"(20\d{2})[-_]?([01]\d)[-_]?([0-3]\d)")


def _sanitize_str(value: object) -> object:
    """Strip NUL bytes from strings so PostgreSQL can store them."""
    if isinstance(value, str):
        return value.replace("\u0000", "")
    return value


def _sanitize_exif(obj: object) -> object:
    """Strip null characters from strings so PostgreSQL JSONB can store them."""
    if isinstance(obj, str):
        return obj.replace("\u0000", "")
    if isinstance(obj, (list, tuple)):
        return type(obj)(_sanitize_exif(item) for item in obj)
    if isinstance(obj, dict):
        return {k: _sanitize_exif(v) for k, v in obj.items()}
    return obj


@dataclass
class DiscoverStats:
    eligible: int = 0
    selected: int = 0
    scanned: int = 0
    upserted: int = 0
    skipped: int = 0
    failed_db: int = 0
    failed_processing: int = 0


@dataclass
class StageStats:
    processed: int = 0


@dataclass(frozen=True)
class DescriptionOptions:
    provider: str = "basic"
    lmstudio_base_url: str = "http://192.168.10.64:1234/v1"
    lmstudio_model: str = "qwen3.6-35b-a3b"
    lmstudio_timeout_seconds: float = 60.0


def _iter_files(roots: Iterable[Path], extensions: set[str]) -> Iterable[tuple[Path, Path]]:
    for root in roots:
        root = root.resolve()
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower().lstrip(".") not in extensions:
                continue
            yield root, path


def _select_discovery_candidates(
    roots: list[Path],
    ext_set: set[str],
    *,
    ingest_limit: int,
    strategy: str,
    seed: int,
) -> tuple[int, list[tuple[Path, Path]]]:
    selected: list[tuple[Path, Path]] = []
    eligible = 0

    if ingest_limit <= 0:
        for candidate in _iter_files(roots, ext_set):
            eligible += 1
            selected.append(candidate)
        return eligible, selected

    rng = random.Random(seed)
    for candidate in _iter_files(roots, ext_set):
        eligible += 1
        if strategy == "random":
            if len(selected) < ingest_limit:
                selected.append(candidate)
                continue

            replacement_idx = rng.randint(0, eligible - 1)
            if replacement_idx < ingest_limit:
                selected[replacement_idx] = candidate
            continue

        if len(selected) < ingest_limit:
            selected.append(candidate)

    return eligible, selected


def _parse_datetime_from_candidate(value: str) -> datetime | None:
    match = DATE_RE.search(value)
    if not match:
        return None
    year, month, day = [int(match.group(i)) for i in range(1, 4)]
    try:
        return datetime(year, month, day, tzinfo=timezone.utc)
    except ValueError:
        return None


def _resolve_taken_at(exif_datetime: str | None, path: Path) -> tuple[datetime, str]:
    if exif_datetime:
        cleaned = exif_datetime.replace(":", "-", 2)
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(cleaned, fmt).replace(tzinfo=timezone.utc), "exif"
            except ValueError:
                continue

    from_name = _parse_datetime_from_candidate(path.name)
    if from_name:
        return from_name, "filename"

    for part in path.parts:
        from_dir = _parse_datetime_from_candidate(part)
        if from_dir:
            return from_dir, "directory"

    return datetime.now(timezone.utc), "ingest_time"


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    text = str(value)
    if "/" in text:
        left, right = text.split("/", maxsplit=1)
        try:
            return float(left) / float(right)
        except (ValueError, ZeroDivisionError):
            return None
    try:
        return float(text)
    except ValueError:
        return None


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


def discover_files(
    db: Database, settings: Settings, roots: list[Path], extensions: list[str]
) -> DiscoverStats:
    if not roots:
        raise ValueError(
            "No roots provided. Set PHOTO_CURATOR_DEFAULT_ROOTS (or PHOTO_INGEST_ROOTS) or pass --roots."
        )

    ext_set = {ext.lower().lstrip(".") for ext in extensions} or SUPPORTED_EXTENSIONS
    stats = DiscoverStats()

    stats.eligible, selected_candidates = _select_discovery_candidates(
        roots,
        ext_set,
        ingest_limit=settings.ingest_limit,
        strategy=settings.ingest_selection_strategy,
        seed=settings.ingest_selection_seed,
    )
    stats.selected = len(selected_candidates)

    logger.info(
        "Discover candidate selection: eligible={eligible} selected={selected} limit={limit} strategy={strategy}",
        eligible=stats.eligible,
        selected=stats.selected,
        limit=settings.ingest_limit,
        strategy=settings.ingest_selection_strategy,
    )

    for root, path in tqdm(selected_candidates, desc="Discovering"):
        stats.scanned += 1
        relative_path = path.relative_to(root).as_posix()

        try:
            logger.info("Processing file: {path}", path=path.name)

            image = open_image(path)
            if image is None:
                logger.warning("Could not open image, skipping: {path}", path=path.name)
                stats.skipped += 1
                continue

            stat = path.stat()
            width, height = image.size
            exif = get_exif(image)

            exif_datetime = exif.get("DateTimeOriginal") or exif.get("DateTime")
            taken_at, taken_source = _resolve_taken_at(exif_datetime, path)

            gps_info = exif.get("GPSInfo") if isinstance(exif.get("GPSInfo"), dict) else {}
            gps_lat = _to_float(gps_info.get("GPSLatitude")) if gps_info else None
            gps_lon = _to_float(gps_info.get("GPSLongitude")) if gps_info else None

            sanitized_exif = _sanitize_exif(exif)
            exif_json_str = json.dumps(sanitized_exif, default=str)

            try:
                db.execute(
                    """
                    INSERT INTO files (
                      source_root, relative_path, filename, extension, mime_type, file_size_bytes,
                      sha256, width, height, orientation, photo_taken_at, photo_taken_at_source,
                      camera_make, camera_model, gps_lat, gps_lon, exif_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                    ON CONFLICT (source_root, relative_path) DO UPDATE SET
                      filename = EXCLUDED.filename,
                      extension = EXCLUDED.extension,
                      mime_type = EXCLUDED.mime_type,
                      file_size_bytes = EXCLUDED.file_size_bytes,
                      sha256 = EXCLUDED.sha256,
                      width = EXCLUDED.width,
                      height = EXCLUDED.height,
                      orientation = EXCLUDED.orientation,
                      photo_taken_at = EXCLUDED.photo_taken_at,
                      photo_taken_at_source = EXCLUDED.photo_taken_at_source,
                      camera_make = EXCLUDED.camera_make,
                      camera_model = EXCLUDED.camera_model,
                      gps_lat = EXCLUDED.gps_lat,
                      gps_lon = EXCLUDED.gps_lon,
                      exif_json = EXCLUDED.exif_json,
                      updated_at = now()
                    """,
                    (
                        str(root),
                        relative_path,
                        path.name,
                        path.suffix.lower().lstrip("."),
                        mimetypes.guess_type(path.name)[0],
                        stat.st_size,
                        sha256_file(path),
                        width,
                        height,
                        exif.get("Orientation"),
                        taken_at,
                        taken_source,
                        _sanitize_str(exif.get("Make")),
                        _sanitize_str(exif.get("Model")),
                        gps_lat,
                        gps_lon,
                        exif_json_str,
                    ),
                )
                logger.info(
                    "File inserted/updated: {filename} size={size}B dims={w}x{h}",
                    filename=path.name,
                    size=stat.st_size,
                    w=width,
                    h=height,
                )
                stats.upserted += 1
            except Exception as db_exc:
                logger.error(
                    "DB insert failed for {filename}: {error}",
                    filename=path.name,
                    error=str(db_exc),
                )
                stats.failed_db += 1

        except Exception as file_exc:
            logger.error(
                "File processing failed for {path}: {error}",
                path=path.name,
                error=str(file_exc),
            )
            stats.failed_processing += 1
    return stats


def _load_image(path: Path, max_size: int = 1024) -> np.ndarray | None:
    image = cv2.imread(str(path))
    if image is None:
        return None
    h, w = image.shape[:2]
    if max(h, w) > max_size:
        scale = max_size / max(h, w)
        image = cv2.resize(image, (int(w * scale), int(h * scale)))
    return image


def _safe_norm(value: float, low: float, high: float) -> float:
    if high - low <= 0:
        return 0.0
    return max(0.0, min(1.0, (value - low) / (high - low)))


def _compute_metrics(
    image: np.ndarray,
) -> tuple[float, float, float, float, float, float, float, float, float]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    blur_score = 1.0 - _safe_norm(lap_var, 100.0, 1200.0)

    brightness = float(np.mean(gray) / 255.0)
    brightness_score = 1.0 - abs(brightness - 0.55)

    contrast_raw = float(np.std(gray) / 255.0)
    contrast_score = _safe_norm(contrast_raw, 0.08, 0.45)

    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).ravel()
    hist /= np.sum(hist) + 1e-8
    entropy = float(-np.sum(hist * np.log2(hist + 1e-12)) / 8.0)

    noise = float(np.std(gray - cv2.GaussianBlur(gray, (3, 3), 0)) / 255.0)
    noise_score = 1.0 - _safe_norm(noise, 0.02, 0.22)

    technical_quality_score = max(
        0.0,
        min(
            1.0,
            (0.30 * (1.0 - blur_score))
            + (0.20 * contrast_score)
            + (0.20 * brightness_score)
            + (0.15 * entropy)
            + (0.15 * noise_score),
        ),
    )
    print_6x8 = max(0.0, min(1.0, technical_quality_score))
    print_8x10 = max(0.0, min(1.0, technical_quality_score * 0.95))
    print_12x18 = max(0.0, min(1.0, technical_quality_score * 0.9))

    return (
        blur_score,
        brightness_score,
        contrast_score,
        entropy,
        noise_score,
        technical_quality_score,
        print_6x8,
        print_8x10,
        print_12x18,
    )


def score_metrics(db: Database, max_size: int = 1024) -> StageStats:
    rows = db.fetchall("SELECT id, source_root, relative_path FROM files ORDER BY id")
    stats = StageStats()

    for file_id, source_root, relative_path in tqdm(rows, desc="Metrics"):
        path = Path(source_root) / Path(relative_path)
        logger.info("Scoring metrics: file_id={id} path={path}", id=file_id, path=path)

        image = _load_image(path, max_size=max_size)
        if image is None:
            logger.warning("Could not load image for metrics, skipping: {path}", path=path)
            continue

        (
            blur_score,
            brightness_score,
            contrast_score,
            entropy_score,
            noise_score,
            technical_quality_score,
            print_6x8,
            print_8x10,
            print_12x18,
        ) = _compute_metrics(image)

        try:
            db.execute(
                """
                INSERT INTO file_metrics (
                  file_id, blur_score, brightness_score, contrast_score, entropy_score, noise_score,
                  technical_quality_score, print_score_6x8, print_score_8x10, print_score_12x18
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (file_id) DO UPDATE SET
                  blur_score = EXCLUDED.blur_score,
                  brightness_score = EXCLUDED.brightness_score,
                  contrast_score = EXCLUDED.contrast_score,
                  entropy_score = EXCLUDED.entropy_score,
                  noise_score = EXCLUDED.noise_score,
                  technical_quality_score = EXCLUDED.technical_quality_score,
                  print_score_6x8 = EXCLUDED.print_score_6x8,
                  print_score_8x10 = EXCLUDED.print_score_8x10,
                  print_score_12x18 = EXCLUDED.print_score_12x18,
                  updated_at = now()
                """,
                (
                    file_id,
                    blur_score,
                    brightness_score,
                    contrast_score,
                    entropy_score,
                    noise_score,
                    technical_quality_score,
                    print_6x8,
                    print_8x10,
                    print_12x18,
                ),
            )
            logger.info(
                "Metrics scored: file_id={id} blur={blur:.3f} brightness={bright:.3f} contrast={contrast:.3f}",
                id=file_id,
                blur=blur_score,
                bright=brightness_score,
                contrast=contrast_score,
            )
            stats.processed += 1
        except Exception as exc:
            logger.error(
                "Metrics DB insert failed for file_id={id}: {error}", id=file_id, error=str(exc)
            )

    logger.info("Metric scoring complete: processed={count}", count=stats.processed)
    return stats


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
               m.technical_quality_score
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
        ) = row

        logger.info("Describing file: file_id={id} filename={name}", id=file_id, name=filename)

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
        lmstudio_used = False
        if resolved_options.provider == "lmstudio":
            photo_path = Path(source_root) / relative_path
            if photo_path.exists():
                try:
                    lmstudio_description = _describe_with_lmstudio(
                        photo_path,
                        filename=filename,
                        camera_make=camera_make,
                        camera_model=camera_model,
                        options=resolved_options,
                    )
                    if lmstudio_description:
                        description_text = lmstudio_description
                        lmstudio_used = True
                except Exception as lm_exc:
                    logger.warning(
                        "LM Studio describe failed for file_id={id}: {error}",
                        id=file_id,
                        error=str(lm_exc),
                    )
            else:
                logger.warning(
                    "Source file not found for description, skipping LM Studio: file_id={id} path={path}",
                    id=file_id,
                    path=photo_path,
                )

        semantic_relevance_score = 0.2
        categories: list[str] = []
        if description_text:
            semantic_relevance_score += min(0.5, len(description_text.split()) / 40.0)
        if camera_make or camera_model:
            semantic_relevance_score += 0.1
        semantic_relevance_score = max(0.0, min(1.0, semantic_relevance_score))

        curation_score = max(
            0.0,
            min(
                1.0,
                (0.7 * (technical_quality_score or print_12x18 or 0.0))
                + (0.3 * semantic_relevance_score),
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

        if lmstudio_used:
            logger.info("Description generated via LM Studio: file_id={id}", id=file_id)
        else:
            logger.debug(
                "Using basic description for file_id={id}: {text}",
                id=file_id,
                text=description_text[:80],
            )

        description_json = {
            "provider": resolved_options.provider,
            "quality_hint": quality_hint,
            "camera_make": camera_make,
            "camera_model": camera_model,
            "scores": {
                "print_12x18": print_12x18,
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
            logger.info(
                "Description saved: file_id={id} provider={provider}",
                id=file_id,
                provider="lmstudio" if lmstudio_used else "basic",
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
