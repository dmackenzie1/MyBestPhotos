from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

from scripts.python_runner_doctor import evaluate_env, parse_dsn


class ParseDsnTests(unittest.TestCase):
    def test_parse_dsn_defaults_port_and_extracts_db(self) -> None:
        host, port, database = parse_dsn("postgresql://user:pass@postgres/photo_curator")
        self.assertEqual(host, "postgres")
        self.assertEqual(port, 5432)
        self.assertEqual(database, "photo_curator")

    def test_parse_dsn_raises_for_bad_input(self) -> None:
        with self.assertRaises(ValueError):
            parse_dsn("not-a-valid-dsn")


class EvaluateEnvTests(unittest.TestCase):
    def test_basic_mode_skips_lmstudio_tcp_and_passes_with_existing_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cache = root / "cache"
            thumbs = cache / "thumbs"
            photo_root = root / "photos"
            thumbs.mkdir(parents=True)
            photo_root.mkdir(parents=True)

            old_env = os.environ.copy()
            try:
                os.environ["PHOTO_CURATOR_DB_DSN"] = (
                    "postgresql://user:pass@localhost:5432/photo_curator"
                )
                os.environ["PHOTO_CURATOR_DEFAULT_ROOTS"] = str(photo_root)
                os.environ["PHOTO_CURATOR_CACHE_DIR"] = str(cache)
                os.environ["PHOTO_CURATOR_THUMBS_DIR"] = str(thumbs)
                os.environ["PHOTO_CURATOR_DESCRIPTION_PROVIDER"] = "basic"

                results = evaluate_env(timeout_seconds=0.05, skip_network=True)
            finally:
                os.environ.clear()
                os.environ.update(old_env)

        by_name = {result.name: result for result in results}
        self.assertTrue(by_name["db_dsn_parse"].ok)
        self.assertTrue(by_name["cache_dir"].ok)
        self.assertTrue(by_name["thumbs_dir"].ok)
        self.assertTrue(by_name["photo_root"].ok)
        self.assertTrue(by_name["description_provider"].ok)


if __name__ == "__main__":
    unittest.main()
