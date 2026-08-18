from datetime import date
from pathlib import Path
import unittest

from post_countdown import TARGET_DATE, get_captions, get_days_remaining, get_image_path


class TestSPMCountdown(unittest.TestCase):
    def test_target_date(self):
        self.assertEqual(TARGET_DATE, date(2026, 11, 23))

    def test_countdown_today(self):
        aug_18 = date(2026, 8, 18)
        self.assertEqual(get_days_remaining(aug_18), 97)
        tw, th = get_captions(97)
        self.assertEqual(tw, "97 days left until #SPM2026")
        self.assertEqual(th, "97 days left until SPM 2026")

    def test_countdown_96_days(self):
        aug_19 = date(2026, 8, 19)
        self.assertEqual(get_days_remaining(aug_19), 96)
        tw, th = get_captions(96)
        self.assertEqual(tw, "96 days left until #SPM2026")
        self.assertEqual(th, "96 days left until SPM 2026")

    def test_countdown_one_day_remaining(self):
        nov_22 = date(2026, 11, 22)
        self.assertEqual(get_days_remaining(nov_22), 1)
        tw, th = get_captions(1)
        self.assertEqual(tw, "1 day left until #SPM2026")
        self.assertEqual(th, "1 day left until SPM 2026")

    def test_countdown_exam_day(self):
        nov_23 = date(2026, 11, 23)
        self.assertEqual(get_days_remaining(nov_23), 0)
        tw, th = get_captions(0)
        self.assertIn("Today is the day", tw)
        self.assertIn("#SPM2026", tw)
        self.assertIn("Today is the day", th)

    def test_image_path_resolution(self):
        base_dir = Path(__file__).resolve().parent
        img_97 = get_image_path(97, base_dir)
        self.assertTrue(img_97.exists(), f"Image 97.png not found at {img_97}")
        self.assertEqual(img_97.name, "97.png")


if __name__ == "__main__":
    unittest.main()
