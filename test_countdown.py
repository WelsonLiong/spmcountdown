from datetime import date
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

import requests

from post_countdown import (
    TARGET_DATE,
    get_captions,
    get_days_remaining,
    get_image_path,
    refresh_threads_token,
)


class TestSPMCountdown(unittest.TestCase):
    def test_target_date(self):
        self.assertEqual(TARGET_DATE, date(2026, 11, 23))

    def test_countdown_100_days(self):
        aug_15 = date(2026, 8, 15)
        self.assertEqual(get_days_remaining(aug_15), 100)
        tw, th = get_captions(100)
        self.assertEqual(tw, "100 days left until #SPM2026")
        self.assertEqual(th, "100 days left until SPM 2026")

    def test_countdown_over_100_days(self):
        aug_14 = date(2026, 8, 14)
        self.assertEqual(get_days_remaining(aug_14), 101)

    def test_countdown_50_days_refresh_target(self):
        oct_4 = date(2026, 10, 4)
        self.assertEqual(get_days_remaining(oct_4), 50)
        tw, th = get_captions(50)
        self.assertEqual(tw, "50 days left until #SPM2026")
        self.assertEqual(th, "50 days left until SPM 2026")

    def test_countdown_today(self):
        aug_18 = date(2026, 8, 18)
        self.assertEqual(get_days_remaining(aug_18), 97)
        tw, th = get_captions(97)
        self.assertEqual(tw, "97 days left until #SPM2026")
        self.assertEqual(th, "97 days left until SPM 2026")

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
        img_96 = get_image_path(96, base_dir)
        self.assertTrue(img_96.exists(), f"Image 96.png not found at {img_96}")
        self.assertEqual(img_96.name, "96.png")

    @patch("post_countdown.requests.get")
    def test_refresh_threads_token_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {
            "access_token": "TH_REFRESHED_MOCK_TOKEN",
            "token_type": "bearer",
            "expires_in": 5184000,
        }
        mock_get.return_value = mock_resp

        result = refresh_threads_token("OLD_TOKEN")
        mock_get.assert_called_once_with(
            "https://graph.threads.com/refresh_access_token",
            params={"grant_type": "th_refresh_token", "access_token": "OLD_TOKEN"},
            timeout=30,
        )
        self.assertEqual(result.get("access_token"), "TH_REFRESHED_MOCK_TOKEN")
        self.assertEqual(result.get("expires_in"), 5184000)

    @patch("post_countdown.requests.get")
    def test_refresh_threads_token_failure(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 400
        mock_resp.text = "OAuthException: Token expired"
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError("400 Client Error")
        mock_get.return_value = mock_resp

        with self.assertRaises(requests.exceptions.HTTPError):
            refresh_threads_token("EXPIRED_TOKEN")


if __name__ == "__main__":
    unittest.main()

