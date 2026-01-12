from __future__ import annotations

from pathlib import Path
import sys

from loguru import logger


def configure_logging(log_dir: str) -> None:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add(Path(log_dir) / "photo_curator.log", rotation="10 MB", level="INFO")
