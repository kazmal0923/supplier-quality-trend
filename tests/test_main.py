"""バッチエントリーポイントのテスト。"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main as app_main
from supplier_quality_trend.monthly_csv import MonthlyCsvError
from supplier_quality_trend.models import WarningItem
from supplier_quality_trend.validation import ValidationError


class MainTest(unittest.TestCase):
    def test_failure_returns_one_and_writes_safe_status(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake_file = root / "main.py"
            with (
                patch.object(app_main, "__file__", str(fake_file)),
                patch.object(
                    app_main,
                    "run_pipeline",
                    side_effect=ValueError("secret path must not be logged"),
                ),
            ):
                result = app_main.main()
            status = json.loads(
                (root / "web/data/update-status.json").read_text(
                    encoding="utf-8"
                )
            )
            log = (root / "logs/error.log").read_text(encoding="ascii")
        self.assertEqual(result, 1)
        self.assertEqual(status["status"], "failure")
        self.assertNotIn("secret", log)

    def test_success_returns_zero(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fake_file = Path(temporary) / "main.py"
            with (
                patch.object(app_main, "__file__", str(fake_file)),
                patch.object(app_main, "run_pipeline"),
            ):
                self.assertEqual(app_main.main(), 0)

    def test_log_write_failure_still_returns_one(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fake_file = Path(temporary) / "main.py"
            with (
                patch.object(app_main, "__file__", str(fake_file)),
                patch.object(
                    app_main,
                    "run_pipeline",
                    side_effect=OSError("pipeline failure"),
                ),
                patch.object(
                    app_main,
                    "_record_failure",
                    side_effect=OSError("log failure"),
                ),
            ):
                self.assertEqual(app_main.main(), 1)

    def test_expected_error_logs_safe_category_without_input_details(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake_file = root / "main.py"
            with (
                patch.object(app_main, "__file__", str(fake_file)),
                patch.object(
                    app_main,
                    "run_pipeline",
                    side_effect=MonthlyCsvError(
                        r"\\server\secret-share\実仕入先名.csv"
                    ),
                ),
            ):
                self.assertEqual(app_main.main(), 1)
            log = (root / "logs/error.log").read_text(encoding="utf-8")
        self.assertIn("MonthlyCsvError", log)
        self.assertIn("Monthly CSV validation failed", log)
        self.assertNotIn("secret-share", log)
        self.assertNotIn("実仕入先名", log)

    def test_validation_failure_logs_sanitized_warning_details(self) -> None:
        error = ValidationError(
            "all rows invalid",
            (
                WarningItem(
                    code="INVALID_HENPIN_SU",
                    message="invalid",
                    source_file="2026年01月.csv",
                    line_number=2,
                    column_name="HENPIN_SU",
                    raw_value="invalid",
                ),
            ),
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake_file = root / "main.py"
            with (
                patch.object(app_main, "__file__", str(fake_file)),
                patch.object(app_main, "run_pipeline", side_effect=error),
            ):
                self.assertEqual(app_main.main(), 1)
            log = (root / "logs/error.log").read_text(encoding="utf-8")
        self.assertIn("2026\\u5e7401\\u6708.csv", log)
        self.assertIn('"line": 2', log)
        self.assertIn('"column": "HENPIN_SU"', log)
        self.assertNotIn(str(root), log)


if __name__ == "__main__":
    unittest.main()
