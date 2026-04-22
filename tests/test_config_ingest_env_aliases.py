from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock

from photo_curator.config import load_settings


class ConfigIngestEnvAliasTests(unittest.TestCase):
    def test_ingest_aliases_are_used_when_photo_curator_vars_unset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "config.toml")
            with open(config_path, "w", encoding="utf-8") as handle:
                handle.write("")

            with mock.patch.dict(
                os.environ,
                {
                    "INGEST_FILE_LIMIT": "123",
                    "INGEST_SELECTION_STRATEGY": "newest",
                },
                clear=False,
            ):
                os.environ.pop("PHOTO_CURATOR_INGEST_LIMIT", None)
                os.environ.pop("PHOTO_CURATOR_INGEST_SELECTION_STRATEGY", None)
                loaded = load_settings(config_path)

            self.assertEqual(loaded.settings.ingest_limit, 123)
            self.assertEqual(loaded.settings.ingest_selection_strategy, "newest")


if __name__ == "__main__":
    unittest.main()
