"""静的画面の表示契約テスト。"""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class WebAssetsTest(unittest.TestCase):
    def test_null_rate_is_displayed_as_unavailable(self) -> None:
        app_source = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        chart_source = (ROOT / "web" / "chart.js").read_text(encoding="utf-8")

        self.assertIn(
            'if (value === null || value === undefined) return "算出不可";',
            app_source,
        )
        self.assertIn(
            'value === null ? "算出不可"',
            chart_source,
        )


if __name__ == "__main__":
    unittest.main()
