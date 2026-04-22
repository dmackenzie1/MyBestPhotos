#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import socket
from typing import Iterable
from urllib.parse import urlparse


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def parse_dsn(dsn: str) -> tuple[str, int, str]:
    parsed = urlparse(dsn)
    if not parsed.hostname:
        raise ValueError(f"Could not parse host from DSN: {dsn}")
    host = parsed.hostname
    port = parsed.port or 5432
    database = parsed.path.lstrip("/") or "<unspecified>"
    return host, port, database


def check_tcp(host: str, port: int, timeout_seconds: float) -> tuple[bool, str]:
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True, f"Connected to {host}:{port}"
    except OSError as exc:
        return False, f"Connection failed to {host}:{port}: {exc}"


def _path_status(path: Path, require_read: bool = False, require_write: bool = False) -> str:
    if not path.exists():
        return "missing"
    if require_read and not os.access(path, os.R_OK):
        return "not readable"
    if require_write and not os.access(path, os.W_OK):
        return "not writable"
    return "ok"


def evaluate_env(timeout_seconds: float, skip_network: bool = False) -> list[CheckResult]:
    dsn = os.getenv("PHOTO_CURATOR_DB_DSN", "postgresql://photo_curator:photo_curator@localhost:5432/photo_curator")
    roots_csv = os.getenv("PHOTO_CURATOR_DEFAULT_ROOTS", "")
    cache_dir = Path(os.getenv("PHOTO_CURATOR_CACHE_DIR", ".cache"))
    thumbs_dir = Path(os.getenv("PHOTO_CURATOR_THUMBS_DIR", ".cache/thumbs"))
    provider = os.getenv("PHOTO_CURATOR_DESCRIPTION_PROVIDER", "basic").strip().lower()
    lmstudio_url = os.getenv("PHOTO_CURATOR_LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1")

    checks: list[CheckResult] = []

    try:
        db_host, db_port, db_name = parse_dsn(dsn)
        checks.append(CheckResult("db_dsn_parse", True, f"Host={db_host} Port={db_port} DB={db_name}"))
    except ValueError as exc:
        checks.append(CheckResult("db_dsn_parse", False, str(exc)))
        db_host = ""
        db_port = 0

    for label, path, writable in (
        ("cache_dir", cache_dir, True),
        ("thumbs_dir", thumbs_dir, True),
    ):
        status = _path_status(path, require_write=writable)
        checks.append(CheckResult(label, status == "ok", f"{path} ({status})"))

    roots = [Path(item.strip()) for item in roots_csv.split(",") if item.strip()]
    if roots:
        for root in roots:
            status = _path_status(root, require_read=True)
            checks.append(CheckResult("photo_root", status == "ok", f"{root} ({status})"))
    else:
        checks.append(
            CheckResult(
                "photo_root",
                False,
                "PHOTO_CURATOR_DEFAULT_ROOTS not set; runner may require --roots or PHOTO_INGEST_ROOTS",
            )
        )

    if provider == "lmstudio":
        parsed = urlparse(lmstudio_url)
        if parsed.hostname:
            lm_port = parsed.port or (443 if parsed.scheme == "https" else 80)
            checks.append(CheckResult("lmstudio_url_parse", True, f"Host={parsed.hostname} Port={lm_port}"))
            if not skip_network:
                ok, detail = check_tcp(parsed.hostname, lm_port, timeout_seconds)
                checks.append(CheckResult("lmstudio_tcp", ok, detail))
        else:
            checks.append(CheckResult("lmstudio_url_parse", False, f"Invalid URL: {lmstudio_url}"))
    else:
        checks.append(CheckResult("description_provider", True, f"{provider} (LM Studio checks skipped)"))

    if not skip_network and db_host:
        ok, detail = check_tcp(db_host, db_port, timeout_seconds)
        checks.append(CheckResult("postgres_tcp", ok, detail))

    return checks


def print_results(results: Iterable[CheckResult]) -> int:
    exit_code = 0
    for item in results:
        icon = "✅" if item.ok else "❌"
        print(f"{icon} {item.name}: {item.detail}")
        if not item.ok:
            exit_code = 1
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight checks for python-runner env/network/path configuration.")
    parser.add_argument("--timeout-seconds", type=float, default=2.0, help="TCP check timeout in seconds")
    parser.add_argument("--skip-network", action="store_true", help="Skip TCP connectivity checks")
    args = parser.parse_args()

    results = evaluate_env(timeout_seconds=args.timeout_seconds, skip_network=args.skip_network)
    return print_results(results)


if __name__ == "__main__":
    raise SystemExit(main())
