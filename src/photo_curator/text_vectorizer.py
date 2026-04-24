from __future__ import annotations

import math
import re

TOKEN_RE = re.compile(r"[a-z0-9]+")
DEFAULT_DIM = 384


def tokenize_text(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def embed_text(text: str, dim: int = DEFAULT_DIM) -> list[float]:
    tokens = tokenize_text(text)
    if not tokens:
        return [0.0] * dim

    vector = [0.0] * dim
    for token in tokens:
        hash_value = 2166136261
        for ch in token:
            hash_value ^= ord(ch)
            hash_value = (hash_value * 16777619) & 0xFFFFFFFF
        bytes_ = [(hash_value >> ((i % 4) * 8)) & 0xFF for i in range(8)]
        slot = (
            int(((bytes_[0] << 24) | (bytes_[1] << 16) | (bytes_[2] << 8) | bytes_[3]) & 0xFFFFFFFF)
            % dim
        )
        sign = -1.0 if bytes_[4] % 2 else 1.0
        weight = 1.0 + min(len(token), 12) / 12.0
        vector[slot] += sign * weight

    norm = math.sqrt(sum(value * value for value in vector))
    if norm <= 1e-9:
        return [0.0] * dim
    return [value / norm for value in vector]


def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"
