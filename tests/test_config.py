"""ローカル設定読込のテスト。"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from supplier_quality_trend.config import SettingsError, load_settings


class SettingsTest(unittest.TestCase):
    def test_relative_paths_are_resolved_from_user_home(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            settings_path = root / "settings.json"
            settings_path.write_text(
                json.dumps(
                    {
                        "monthly_csv_directory": "Box/monthly",
                        "supplier_master_file": "Box/仕入先マスタ_絞り込み無し.csv",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            with patch("supplier_quality_trend.config.Path.home", return_value=root):
                settings = load_settings(settings_path)
            self.assertEqual(settings.monthly_csv_directory, root / "Box/monthly")
            self.assertEqual(
                settings.supplier_master_file,
                root / "Box/仕入先マスタ_絞り込み無し.csv",
            )

    def test_placeholder_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "settings.json"
            path.write_text(
                json.dumps(
                    {
                        "monthly_csv_directory": "<MONTHLY>",
                        "supplier_master_file": "master.csv",
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(SettingsError):
                load_settings(path)


if __name__ == "__main__":
    unittest.main()
