from __future__ import annotations

import heapq
from pathlib import Path
import random

from photo_curator.pipeline_v1.common import _iter_files


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

    if strategy == "newest":
        newest_heap: list[tuple[float, str, Path, Path]] = []
        for root, path in _iter_files(roots, ext_set):
            eligible += 1
            mtime = path.stat().st_mtime
            comparable = (mtime, str(path), root, path)
            if len(newest_heap) < ingest_limit:
                heapq.heappush(newest_heap, comparable)
            else:
                heapq.heappushpop(newest_heap, comparable)

        newest_heap.sort(reverse=True)
        return eligible, [(root, path) for _, _, root, path in newest_heap]

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


def _should_skip_due_to_duplicate_cap(
    *,
    existing_path_record: bool,
    filename_count: int,
    sha_count: int,
    duplicate_cap: int,
) -> bool:
    if existing_path_record:
        return False
    return filename_count >= duplicate_cap or sha_count >= duplicate_cap
