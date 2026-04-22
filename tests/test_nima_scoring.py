from __future__ import annotations

import unittest

from photo_curator.pipeline_v1 import _compute_nima_style_score, _derive_aesthetic_and_keep_scores


class NimaScoringTests(unittest.TestCase):
    def test_nima_outputs_stay_in_unit_interval(self) -> None:
        nima_score, aesthetic_score, keep_score = _compute_nima_style_score(
            blur_score=0.2,
            brightness_score=0.7,
            contrast_score=0.6,
            entropy_score=0.5,
            technical_quality_score=0.75,
            composition_balance_score=0.8,
        )
        self.assertGreaterEqual(nima_score, 0.0)
        self.assertLessEqual(nima_score, 1.0)
        self.assertGreaterEqual(aesthetic_score, 0.0)
        self.assertLessEqual(aesthetic_score, 1.0)
        self.assertGreaterEqual(keep_score, 0.0)
        self.assertLessEqual(keep_score, 1.0)

    def test_higher_inputs_raise_nima_score(self) -> None:
        low, _, _ = _compute_nima_style_score(
            blur_score=0.7,
            brightness_score=0.3,
            contrast_score=0.2,
            entropy_score=0.2,
            technical_quality_score=0.2,
            composition_balance_score=0.2,
        )
        high, _, _ = _compute_nima_style_score(
            blur_score=0.1,
            brightness_score=0.8,
            contrast_score=0.8,
            entropy_score=0.8,
            technical_quality_score=0.8,
            composition_balance_score=0.8,
        )
        self.assertGreater(high, low)

    def test_derived_scores_increase_with_nima_signal(self) -> None:
        aesthetic_low, keep_low = _derive_aesthetic_and_keep_scores(
            nima_score=0.25,
            technical_quality_score=0.7,
            blur_score=0.3,
        )
        aesthetic_high, keep_high = _derive_aesthetic_and_keep_scores(
            nima_score=0.8,
            technical_quality_score=0.7,
            blur_score=0.3,
        )
        self.assertGreater(aesthetic_high, aesthetic_low)
        self.assertGreater(keep_high, keep_low)


if __name__ == "__main__":
    unittest.main()
