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

    def test_entity_options_use_numeric_supplier_id_sort(self) -> None:
        app_source = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn("function supplierIdSortKey(supplierId)", app_source)
        self.assertIn(r"/^\d+$/.test(trimmed)", app_source)

    def test_feature_002_multi_select_and_category_totals_hooks(self) -> None:
        app_source = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        html_source = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        combine_source = (ROOT / "web" / "combine.js").read_text(encoding="utf-8")
        self.assertIn('option value="category"', html_source)
        self.assertIn('id="select-all"', html_source)
        self.assertIn('id="clear-selection"', html_source)
        self.assertIn("selectAll", app_source)
        self.assertIn("combine.js", html_source)
        self.assertIn("function combineEntityMonths", combine_source)
        self.assertIn('mode === "category"', app_source)
        self.assertIn("suppliersInCategory", app_source)
        self.assertIn("selectedSupplierIds", app_source)


if __name__ == "__main__":
    unittest.main()
