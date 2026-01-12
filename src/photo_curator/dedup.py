from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from loguru import logger
import imagehash
from PIL import Image
from tqdm import tqdm

from photo_curator.db import Database


@dataclass
class DedupStats:
    clusters: int = 0
    members: int = 0


def _score_row(row: tuple[float | None, float | None, float | None]) -> float:
    sharpness, contrast, aesthetic = row
    return float((sharpness or 0.0) * 0.4 + (contrast or 0.0) * 10.0 + (aesthetic or 0.0) * 2.0)


def dedup(db: Database, thumbs_dir: str, threshold: int = 6) -> DedupStats:
    rows = db.fetchall(
        """
        SELECT p.id, p.sha256, m.sharpness, m.contrast, m.aesthetic_score
        FROM photos p
        LEFT JOIN metrics m ON m.photo_id = p.id
        """
    )

    hashes: list[tuple[imagehash.ImageHash, list[int]]] = []
    stats = DedupStats()

    for photo_id, sha256, sharpness, contrast, aesthetic in tqdm(rows, desc="Deduplicating"):
        thumb_path = Path(thumbs_dir) / f"{sha256}.jpg"
        if not thumb_path.exists():
            continue
        with Image.open(thumb_path) as image:
            phash = imagehash.phash(image)

        matched = False
        for idx, (existing_hash, members) in enumerate(hashes):
            if phash - existing_hash <= threshold:
                members.append(photo_id)
                hashes[idx] = (existing_hash, members)
                matched = True
                break
        if not matched:
            hashes.append((phash, [photo_id]))

    for phash, members in hashes:
        if len(members) <= 1:
            continue
        cluster_id = db.fetchall(
            "INSERT INTO clusters (method) VALUES (%s) RETURNING id",
            ("phash",),
        )[0][0]
        stats.clusters += 1

        scores = db.fetchall(
            """
            SELECT p.id, m.sharpness, m.contrast, m.aesthetic_score
            FROM photos p
            LEFT JOIN metrics m ON m.photo_id = p.id
            WHERE p.id = ANY(%s)
            """,
            (members,),
        )
        scored = sorted(scores, key=lambda row: _score_row((row[1], row[2], row[3])), reverse=True)

        for photo_id, *_ in scored:
            db.execute(
                "INSERT INTO cluster_members (cluster_id, photo_id) VALUES (%s, %s)",
                (cluster_id, photo_id),
            )
            stats.members += 1

    logger.info("Dedup complete: clusters={clusters}, members={members}", **stats.__dict__)
    return stats
