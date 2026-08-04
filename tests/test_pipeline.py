"""入力からJSON生成までの統合テスト。"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from supplier_quality_trend.monthly_csv import MonthlyCsvError
from supplier_quality_trend.pipeline import run_pipeline
from supplier_quality_trend.validation import ValidationError


class PipelineTest(unittest.TestCase):
    def _prepare_root(self, root: Path) -> Path:
        monthly = root / "input/monthly"
        monthly.mkdir(parents=True)
        (monthly / "2026年01月.csv").write_text(
            "SHIIRESAKI_ID,SHIIRESAKI_NM,HENPIN_SU,"
            "SYUKKA_SU,DEFECTIVE_RATE\n"
            "S001,旧架空仕入先A,1,100,0.01\n",
            encoding="utf-8",
        )
        master = root / "input/仕入先マスタ_絞り込み無し.csv"
        master.write_bytes(
            (
                "DISPLAY_NM_1,SHIIRESAKI_ID,SHIIRESAKI_NM1\r\n"
                "国内仕入れ,S001,架空仕入先A\r\n"
            ).encode("cp932")
        )
        config = root / "config"
        config.mkdir()
        (config / "settings.json").write_text(
            json.dumps(
                {
                    "monthly_csv_directory": str(monthly),
                    "supplier_master_file": str(master),
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (config / "supplier-name-aliases.csv").write_text(
            "CANONICAL_GROUP_NM,ALIAS_SUPPLIER_NM,ENABLED,NOTE\n",
            encoding="utf-8",
        )
        return monthly

    def test_pipeline_generates_dashboard_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._prepare_root(root)
            run_pipeline(root)
            dashboard_path = root / "web/data/dashboard-data.json"
            dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
            self.assertEqual(dashboard["latestDataMonth"], "2026-01")
            self.assertTrue(dashboard["entities"])

    def test_failed_update_keeps_previous_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            monthly = self._prepare_root(root)
            run_pipeline(root)
            dashboard_path = root / "web/data/dashboard-data.json"
            previous = dashboard_path.read_bytes()

            (monthly / "2026年01月.csv").write_text(
                "SHIIRESAKI_ID\nS001\n",
                encoding="utf-8",
            )
            with self.assertRaises(MonthlyCsvError):
                run_pipeline(root)
            self.assertEqual(dashboard_path.read_bytes(), previous)

    def test_short_row_with_no_valid_rows_keeps_previous_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            monthly = self._prepare_root(root)
            run_pipeline(root)
            dashboard_path = root / "web/data/dashboard-data.json"
            previous = dashboard_path.read_bytes()

            (monthly / "2026年01月.csv").write_text(
                "SHIIRESAKI_ID,SHIIRESAKI_NM,HENPIN_SU,"
                "SYUKKA_SU,DEFECTIVE_RATE\n"
                "S001,旧架空仕入先A,1\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValidationError) as context:
                run_pipeline(root)
            self.assertEqual(
                context.exception.warnings[0].code,
                "INVALID_SYUKKA_SU",
            )
            self.assertEqual(dashboard_path.read_bytes(), previous)

    def test_short_quantity_row_is_excluded_with_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            monthly = self._prepare_root(root)
            (monthly / "2026年01月.csv").write_text(
                "SHIIRESAKI_ID,SHIIRESAKI_NM,HENPIN_SU,"
                "SYUKKA_SU,DEFECTIVE_RATE\n"
                "S001,旧架空仕入先A,1\n"
                "S002,架空仕入先B,2,100,0.02\n",
                encoding="utf-8",
            )
            run_pipeline(root)
            dashboard = json.loads(
                (root / "web/data/dashboard-data.json").read_text(
                    encoding="utf-8"
                )
            )
        self.assertNotIn(
            "supplier:S001",
            {entity["entityId"] for entity in dashboard["entities"]},
        )
        self.assertIn(
            "INVALID_SYUKKA_SU",
            {warning["code"] for warning in dashboard["warnings"]},
        )

    def test_empty_defective_rate_recalculates_from_quantities(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            monthly = self._prepare_root(root)
            (monthly / "2026年01月.csv").write_text(
                "SHIIRESAKI_ID,SHIIRESAKI_NM,HENPIN_SU,"
                "SYUKKA_SU,DEFECTIVE_RATE\n"
                "S001,旧架空仕入先A,1,100,\n",
                encoding="utf-8",
            )
            run_pipeline(root)
            dashboard = json.loads(
                (root / "web/data/dashboard-data.json").read_text(
                    encoding="utf-8"
                )
            )
        supplier = next(
            entity
            for entity in dashboard["entities"]
            if entity["entityId"] == "supplier:S001"
        )
        self.assertEqual(supplier["months"][-1]["defectiveRate"], "0.01")
        self.assertIn(
            "INVALID_DEFECTIVE_RATE",
            {warning["code"] for warning in dashboard["warnings"]},
        )


if __name__ == "__main__":
    unittest.main()
