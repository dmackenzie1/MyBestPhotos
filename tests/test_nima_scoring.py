from __future__ import annotations

import unittest

from photo_curator.pipeline_v1.scoring import compute_clip_aesthetic


class ClipAestheticScoringTests(unittest.TestCase):
    def test_outputs_stay_in_unit_interval(self) -> None:
        clip_aesthetic_score, aesthetic_score, keep_score = compute_clip_aesthetic(
            clip_score=0.7,
            composition_balance_score=0.8,
            blur_score=0.2,
            technical_quality_score=0.75,
        )
        self.assertGreaterEqual(clip_aesthetic_score, 0.0)
        self.assertLessEqual(clip_aesthetic_score, 1.0)
        self.assertGreaterEqual(aesthetic_score, 0.0)
        self.assertLessEqual(aesthetic_score, 1.0)
        self.assertGreaterEqual(keep_score, 0.0)
        self.assertLessEqual(keep_score, 1.0)

    def test_higher_inputs_raise_clip_score(self) -> None:
        low, _, _ = compute_clip_aesthetic(
            clip_score=0.2,
            composition_balance_score=0.2,
            blur_score=0.7,
            technical_quality_score=0.2,
        )
        high, _, _ = compute_clip_aesthetic(
            clip_score=0.8,
            composition_balance_score=0.8,
            blur_score=0.1,
            technical_quality_score=0.8,
        )
        self.assertGreater(high, low)


if __name__ == "__main__":
    unittest.main()
