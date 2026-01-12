from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Photo(BaseModel):
    id: int
    path: str
    sha256: str
    mtime: datetime
    size_bytes: int
    width: Optional[int] = None
    height: Optional[int] = None
    exif_datetime: Optional[datetime] = None
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    lens: Optional[str] = None
    iso: Optional[int] = None
    shutter: Optional[str] = None
    aperture: Optional[str] = None
    focal_length: Optional[str] = None


class Metric(BaseModel):
    photo_id: int
    sharpness: Optional[float] = None
    exposure_clip_hi: Optional[float] = None
    exposure_clip_lo: Optional[float] = None
    contrast: Optional[float] = None
    noise_proxy: Optional[float] = None
    aesthetic_score: Optional[float] = None
    face_count: Optional[int] = None


class Embedding(BaseModel):
    photo_id: int
    model_name: str
    embedding: list[float]
