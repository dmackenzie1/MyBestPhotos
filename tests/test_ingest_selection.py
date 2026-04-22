from __future__ import annotations

from pathlib import Path
import os
import tempfile
import unittest

from photo_curator.pipeline_v1 import _select_discovery_candidates


class IngestSelectionTests(unittest.TestCase):
    def test_first_strategy_picks_first_n_and_counts_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for idx in range(5):
                (root / f"img_{idx}.jpg").write_bytes(b"jpg")

            eligible, selected = _select_discovery_candidates(
                [root],
                {"jpg"},
                ingest_limit=3,
                strategy="first",
                seed=123,
            )

            self.assertEqual(eligible, 5)
            self.assertEqual(len(selected), 3)
            self.assertEqual(len({path.name for _, path in selected}), 3)
            self.assertTrue(all(path.name.startswith("img_") for _, path in selected))

    def test_random_strategy_is_seeded_and_stable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for idx in range(10):
                (root / f"img_{idx}.jpg").write_bytes(b"jpg")

            eligible_1, selected_1 = _select_discovery_candidates(
                [root],
                {"jpg"},
                ingest_limit=4,
                strategy="random",
                seed=42,
            )
            eligible_2, selected_2 = _select_discovery_candidates(
                [root],
                {"jpg"},
                ingest_limit=4,
                strategy="random",
                seed=42,
            )

            self.assertEqual(eligible_1, 10)
            self.assertEqual(eligible_2, 10)
            self.assertEqual(
                [path.name for _, path in selected_1], [path.name for _, path in selected_2]
            )

    def test_zero_limit_includes_all_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for idx in range(4):
                (root / f"img_{idx}.jpg").write_bytes(b"jpg")

            eligible, selected = _select_discovery_candidates(
                [root],
                {"jpg"},
                ingest_limit=0,
                strategy="first",
                seed=1,
            )

            self.assertEqual(eligible, 4)
            self.assertEqual(len(selected), 4)

    def test_newest_strategy_picks_most_recent_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            paths: list[Path] = []
            for idx in range(5):
                path = root / f"img_{idx}.jpg"
                path.write_bytes(b"jpg")
                paths.append(path)

            for idx, path in enumerate(paths):
                ts = 1_700_000_000 + idx
                os.utime(path, (ts, ts))

            eligible, selected = _select_discovery_candidates(
                [root],
                {"jpg"},
                ingest_limit=2,
                strategy="newest",
                seed=7,
            )

            self.assertEqual(eligible, 5)
            self.assertEqual(len(selected), 2)
            self.assertEqual([path.name for _, path in selected], ["img_4.jpg", "img_3.jpg"])


if __name__ == "__main__":
    unittest.main()
