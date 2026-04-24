from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import unittest

from photo_curator.pipeline_v1.common import _resolve_taken_at


class TakenAtResolutionTests(unittest.TestCase):
    def test_prefers_exif_datetime_when_present(self) -> None:
        taken_at, source = _resolve_taken_at(
            "2009:12:15 08:30:01", Path("/photos/library/image.jpg")
        )

        self.assertEqual(taken_at, datetime(2009, 12, 15, 8, 30, 1, tzinfo=timezone.utc))
        self.assertEqual(source, "exif")

    def test_infers_year_month_from_directory_when_day_is_missing(self) -> None:
        taken_at, source = _resolve_taken_at(
            None,
            Path("/photos/library/2009/2009-12/l_84890506657140a4bc71b2cbab362ed5.jpg"),
        )

        self.assertEqual(taken_at, datetime(2009, 12, 1, tzinfo=timezone.utc))
        self.assertEqual(source, "directory_month")

    def test_infers_date_from_directory_with_text_prefix_or_suffix(self) -> None:
        taken_at, source = _resolve_taken_at(
            None,
            Path("/photos/library/raw-trip-2014-07-03-edited/IMG_001.jpg"),
        )

        self.assertEqual(taken_at, datetime(2014, 7, 3, tzinfo=timezone.utc))
        self.assertEqual(source, "directory")

    def test_does_not_treat_compact_digit_runs_as_date(self) -> None:
        taken_at, source = _resolve_taken_at(
            None,
            Path("/photos/library/20140703/84890506657140a4bc71b2cbab362ed5.jpg"),
        )

        self.assertIsNone(taken_at)
        self.assertIsNone(source)

    def test_returns_none_when_no_exif_or_date_hints_exist(self) -> None:
        taken_at, source = _resolve_taken_at(None, Path("/photos/library/misc/random_name.jpg"))

        self.assertIsNone(taken_at)
        self.assertIsNone(source)


if __name__ == "__main__":
    unittest.main()
