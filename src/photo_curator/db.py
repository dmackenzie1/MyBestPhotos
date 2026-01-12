from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from loguru import logger
import psycopg
from psycopg_pool import ConnectionPool


class Database:
    def __init__(self, dsn: str) -> None:
        self._pool = ConnectionPool(conninfo=dsn, min_size=1, max_size=5, open=True)

    @contextmanager
    def connection(self) -> Iterator[psycopg.Connection]:
        with self._pool.connection() as conn:
            yield conn

    def close(self) -> None:
        self._pool.close()

    def check(self) -> None:
        try:
            with self.connection() as conn:
                conn.execute("SELECT 1")
        except Exception as exc:  # noqa: BLE001
            logger.error("Database check failed: {error}", error=str(exc))
            raise

    def fetchall(self, query: str, params: tuple[Any, ...] | None = None) -> list[Any]:
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                return cur.fetchall()

    def execute(self, query: str, params: tuple[Any, ...] | None = None) -> None:
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                conn.commit()
