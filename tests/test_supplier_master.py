"""仕入先マスタ読込・結合のテスト。"""

from __future__ import annotations

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from supplier_quality_trend.models import MonthlyRecord
from supplier_quality_trend.supplier_master import (
    join_supplier_master,
    read_supplier_master,
)


class SupplierMasterTest(unittest.TestCase):
    def _write_master(self, directory: Path) -> Path:
        path = directory / "仕入先マスタ_絞り込み無し.csv"
        content = (
            "DISPLAY_NM_1,SHIIRESAKI_ID,SHIIRESAKI_NM1\r\n"
            "国内仕入れ,S001,現在の架空仕入先A\r\n"
        )
        path.write_bytes(content.encode("cp932"))
        return path

    def test_reads_cp932_master(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            master = read_supplier_master(self._write_master(Path(temporary)))
            self.assertEqual(master["S001"].category, "国内仕入れ")
            self.assertEqual(master["S001"].current_name, "現在の架空仕入先A")

    def test_join_uses_current_name_and_warns_name_change(self) -> None:
        record = MonthlyRecord(
            source_path=Path("2026年01月.csv"),
            target_month="2026-01",
            supplier_id="S001",
            historical_name="旧架空仕入先A",
            return_quantity=Decimal("1"),
            shipment_quantity=Decimal("100"),
            source_rate=Decimal("0.01"),
        )
        with tempfile.TemporaryDirectory() as temporary:
            master = read_supplier_master(self._write_master(Path(temporary)))
            normalized, warnings = join_supplier_master((record,), master)
        self.assertEqual(normalized[0].current_name, "現在の架空仕入先A")
        self.assertEqual(warnings[0].code, "SUPPLIER_NAME_CHANGED")

    def test_unregistered_supplier_is_kept_with_warning(self) -> None:
        record = MonthlyRecord(
            source_path=Path("2026年01月.csv"),
            target_month="2026-01",
            supplier_id="S999",
            historical_name="未登録架空仕入先",
            return_quantity=Decimal("1"),
            shipment_quantity=Decimal("10"),
            source_rate=Decimal("0.1"),
        )
        normalized, warnings = join_supplier_master((record,), {})
        self.assertEqual(normalized[0].current_name, "未登録架空仕入先")
        self.assertFalse(normalized[0].master_registered)
        self.assertEqual(warnings[0].code, "MASTER_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
