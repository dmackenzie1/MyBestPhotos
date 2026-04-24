from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any, Iterable

DATE_RE = re.compile(r"(?<!\d)(20\d{2})[-_](0[1-9]|1[0-2])[-_](0[1-9]|[12]\d|3[01])(?!\d)")
YEAR_MONTH_RE = re.compile(r"(?<!\d)(20\d{2})[-_](0[1-9]|1[0-2])(?!\d)")
YEAR_RE = re.compile(r"(?<!\d)(20\d{2})(?!\d)")


def _sanitize_str(value: object) -> object:
    """Strip NUL bytes from strings so PostgreSQL can store them."""
    if isinstance(value, str):
        return value.replace("\u0000", "")
    return value


def _encode_exif_bytes(raw: bytes) -> dict[str, str]:
    """Encode binary EXIF blobs into compact JSON-safe hex text."""
    return {"__type__": "bytes_hex", "value": raw.hex()}


def _sanitize_exif(obj: object) -> object:
    """Normalize EXIF payloads for JSONB: strip NULs and encode binary values."""
    if isinstance(obj, str):
        return obj.replace("\u0000", "")
    if isinstance(obj, bytes):
        return _encode_exif_bytes(obj)
    if isinstance(obj, (list, tuple)):
        return [_sanitize_exif(item) for item in obj]
    if isinstance(obj, dict):
        return {str(k): _sanitize_exif(v) for k, v in obj.items()}
    return obj


def _iter_files(roots: Iterable[Path], extensions: set[str]) -> Iterable[tuple[Path, Path]]:
    for root in roots:
        root = root.resolve()
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower().lstrip(".") not in extensions:
                continue
            yield root, path


def _parse_datetime_from_candidate(value: str) -> datetime | None:
    match = DATE_RE.search(value)
    if not match:
        return None
    year, month, day = [int(match.group(i)) for i in range(1, 4)]
    try:
        return datetime(year, month, day, tzinfo=timezone.utc)
    except ValueError:
        return None


def _parse_month_from_candidate(value: str) -> datetime | None:
    match = YEAR_MONTH_RE.search(value)
    if not match:
        return None
    year, month = [int(match.group(i)) for i in range(1, 3)]
    try:
        return datetime(year, month, 1, tzinfo=timezone.utc)
    except ValueError:
        return None


def _parse_year_from_candidate(value: str) -> datetime | None:
    match = YEAR_RE.search(value)
    if not match:
        return None
    try:
        return datetime(int(match.group(1)), 1, 1, tzinfo=timezone.utc)
    except ValueError:
        return None


def _resolve_taken_at(exif_datetime: str | None, path: Path) -> tuple[datetime | None, str | None]:
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

    for part in reversed(path.parent.parts):
        from_dir = _parse_datetime_from_candidate(part)
        if from_dir:
            return from_dir, "directory"

    month_from_name = _parse_month_from_candidate(path.name)
    if month_from_name:
        return month_from_name, "filename_month"

    for part in reversed(path.parent.parts):
        month_from_dir = _parse_month_from_candidate(part)
        if month_from_dir:
            return month_from_dir, "directory_month"

    year_from_name = _parse_year_from_candidate(path.name)
    if year_from_name:
        return year_from_name, "filename_year"

    for part in reversed(path.parent.parts):
        year_from_dir = _parse_year_from_candidate(part)
        if year_from_dir:
            return year_from_dir, "directory_year"

    return None, None


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


def _load_image(path: Path, max_size: int = 1024) -> Any:
    import cv2

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
