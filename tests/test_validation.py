"""月次値の型変換・警告テスト。"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from pathlib import Path

from supplier_quality_trend.monthly_csv import MonthlyCsvData
from supplier_quality_trend.validation import (
    ValidationError,
    parse_monthly_records,
    resolve_run_month,
)


class ValidationTest(unittest.TestCase):
    def _row(self, **overrides: str) -> dict[str, str]:
        row = {
            "SHIIRESAKI_ID": "S001",
            "SHIIRESAKI_NM": "架空仕入先A",
            "HENPIN_SU": "1",
            "SYUKKA_SU": "100",
            "DEFECTIVE_RATE": "0.01",
        }
        row.update(overrides)
        return row

    def _file(
        self,
        *rows: dict[str, str],
        target_month: str = "2026-01",
        filename: str | None = None,
    ) -> MonthlyCsvData:
        name = filename or f"{target_month[:4]}年{target_month[5:]}月.csv"
        return MonthlyCsvData(
            source_path=Path(name),
            target_month=target_month,
            rows=rows or (self._row(),),
        )

    def _valid_row(self) -> dict[str, str]:
        return self._row(SHIIRESAKI_ID="S002", SHIIRESAKI_NM="架空仕入先B")

    def _parse(
        self,
        files: tuple[MonthlyCsvData, ...],
        *,
        run_month: str = "2026-08",
    ):
        return parse_monthly_records(files, run_month=run_month)

    def test_integer_quantity_is_valid(self) -> None:
        records, warnings = self._parse(
            (
                self._file(
                    self._row(
                        HENPIN_SU="1",
                        SYUKKA_SU="25",
                        DEFECTIVE_RATE="0.04",
                    )
                ),
            )
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(str(records[0].return_quantity), "1")
        self.assertEqual(str(records[0].shipment_quantity), "25")
        self.assertFalse(
            any(warning.code.startswith("INVALID_") for warning in warnings)
        )

    def test_decimal_notation_integer_quantities_are_valid(self) -> None:
        records, warnings = self._parse(
            (
                self._file(
                    self._row(
                        HENPIN_SU="1.0",
                        SYUKKA_SU="2.00",
                        DEFECTIVE_RATE="0.5",
                    )
                ),
            )
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(str(records[0].return_quantity), "1.0")
        self.assertEqual(str(records[0].shipment_quantity), "2.00")
        self.assertFalse(
            any(warning.code.startswith("INVALID_") for warning in warnings)
        )

    def test_non_integer_quantities_exclude_row_with_warnings(self) -> None:
        records, warnings = self._parse(
            (
                self._file(
                    self._row(HENPIN_SU="1.5", SYUKKA_SU="0.25"),
                    self._valid_row(),
                ),
            )
        )
        self.assertEqual([record.supplier_id for record in records], ["S002"])
        self.assertEqual(
            [
                (warning.column_name, warning.raw_value)
                for warning in warnings
            ],
            [("HENPIN_SU", "1.5"), ("SYUKKA_SU", "0.25")],
        )

    def test_empty_henpin_su_excludes_row_with_warning_details(self) -> None:
        records, warnings = self._parse(
            (self._file(self._row(HENPIN_SU=""), self._valid_row()),)
        )
        self.assertEqual([record.supplier_id for record in records], ["S002"])
        warning = warnings[0]
        self.assertEqual(warning.code, "INVALID_HENPIN_SU")
        self.assertEqual(warning.source_file, "2026年01月.csv")
        self.assertEqual(warning.line_number, 2)
        self.assertEqual(warning.column_name, "HENPIN_SU")
        self.assertEqual(warning.raw_value, "")

    def test_empty_syukka_su_excludes_row(self) -> None:
        records, warnings = self._parse(
            (self._file(self._row(SYUKKA_SU=""), self._valid_row()),)
        )
        self.assertEqual([record.supplier_id for record in records], ["S002"])
        self.assertEqual(warnings[0].code, "INVALID_SYUKKA_SU")
        self.assertEqual(warnings[0].raw_value, "")

    def test_non_numeric_quantity_excludes_row(self) -> None:
        records, warnings = self._parse(
            (self._file(self._row(HENPIN_SU="invalid"), self._valid_row()),)
        )
        self.assertEqual([record.supplier_id for record in records], ["S002"])
        self.assertEqual(warnings[0].code, "INVALID_HENPIN_SU")
        self.assertEqual(warnings[0].raw_value, "invalid")

    def test_negative_quantity_excludes_row(self) -> None:
        records, warnings = self._parse(
            (self._file(self._row(SYUKKA_SU="-1"), self._valid_row()),)
        )
        self.assertEqual([record.supplier_id for record in records], ["S002"])
        self.assertEqual(warnings[0].code, "INVALID_SYUKKA_SU")
        self.assertEqual(warnings[0].raw_value, "-1")

    def test_both_invalid_quantities_record_two_warnings_once(self) -> None:
        records, warnings = self._parse(
            (
                self._file(
                    self._row(HENPIN_SU="", SYUKKA_SU="invalid"),
                    self._valid_row(),
                ),
            )
        )
        self.assertEqual([record.supplier_id for record in records], ["S002"])
        self.assertEqual(
            [warning.column_name for warning in warnings],
            ["HENPIN_SU", "SYUKKA_SU"],
        )

    def test_month_with_no_valid_rows_fails(self) -> None:
        invalid_file = self._file(self._row(HENPIN_SU=""))
        with self.assertRaises(ValidationError) as context:
            self._parse((invalid_file,))
        self.assertEqual(len(context.exception.warnings), 1)
        self.assertEqual(
            context.exception.warnings[0].code,
            "INVALID_HENPIN_SU",
        )

    def test_current_month_with_only_invalid_rows_fails(self) -> None:
        invalid_file = self._file(
            self._row(HENPIN_SU=""),
            target_month="2026-08",
        )
        with self.assertRaises(ValidationError) as context:
            self._parse((invalid_file,), run_month="2026-08")
        self.assertEqual(
            context.exception.warnings[0].code,
            "INVALID_HENPIN_SU",
        )

    def test_zero_shipment_is_included_with_warning(self) -> None:
        records, warnings = self._parse(
            (self._file(self._row(HENPIN_SU="2", SYUKKA_SU="0")),)
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(str(records[0].return_quantity), "2")
        self.assertEqual(str(records[0].shipment_quantity), "0")
        self.assertIn(
            "ZERO_SHIPMENT_QUANTITY",
            {warning.code for warning in warnings},
        )

    def test_defective_rate_micro_difference_is_allowed(self) -> None:
        _, warnings = self._parse(
            (self._file(self._row(DEFECTIVE_RATE="0.010000000001")),)
        )
        self.assertNotIn(
            "DEFECTIVE_RATE_MISMATCH",
            {warning.code for warning in warnings},
        )

    def test_clear_defective_rate_mismatch_is_warning(self) -> None:
        _, warnings = self._parse(
            (self._file(self._row(DEFECTIVE_RATE="0.010000000002")),)
        )
        self.assertIn(
            "DEFECTIVE_RATE_MISMATCH",
            {warning.code for warning in warnings},
        )

    def test_empty_defective_rate_warns_and_keeps_row(self) -> None:
        records, warnings = self._parse(
            (self._file(self._row(DEFECTIVE_RATE="")),)
        )
        self.assertEqual(len(records), 1)
        self.assertIsNone(records[0].source_rate)
        self.assertIn(
            "INVALID_DEFECTIVE_RATE",
            {warning.code for warning in warnings},
        )

    def test_empty_past_monthly_file_fails(self) -> None:
        empty_file = MonthlyCsvData(
            source_path=Path("2026年01月.csv"),
            target_month="2026-01",
            rows=(),
        )
        with self.assertRaises(ValidationError) as context:
            self._parse((empty_file,), run_month="2026-08")
        self.assertEqual(
            context.exception.warnings[0].code,
            "EMPTY_MONTHLY_FILE",
        )
        self.assertEqual(
            context.exception.warnings[0].source_file,
            "2026年01月.csv",
        )

    def test_empty_current_monthly_file_is_warning_and_continues(self) -> None:
        past_file = self._file(target_month="2026-07")
        empty_current = MonthlyCsvData(
            source_path=Path("2026年08月.csv"),
            target_month="2026-08",
            rows=(),
        )
        records, warnings = self._parse(
            (past_file, empty_current),
            run_month="2026-08",
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].target_month, "2026-07")
        self.assertEqual(warnings[0].code, "EMPTY_CURRENT_MONTH_FILE")
        self.assertEqual(warnings[0].source_file, "2026年08月.csv")
        self.assertEqual(warnings[0].target_month, "2026-08")

    def test_empty_current_monthly_file_alone_fails(self) -> None:
        empty_current = MonthlyCsvData(
            source_path=Path("2026年08月.csv"),
            target_month="2026-08",
            rows=(),
        )
        with self.assertRaises(ValidationError) as context:
            self._parse((empty_current,), run_month="2026-08")
        self.assertEqual(
            context.exception.warnings[0].code,
            "EMPTY_CURRENT_MONTH_FILE",
        )

    def test_resolve_run_month_uses_jst(self) -> None:
        # UTC 2026-07-31 15:00 → JST 2026-08-01 00:00
        self.assertEqual(
            resolve_run_month(
                datetime(2026, 7, 31, 15, 0, tzinfo=timezone.utc)
            ),
            "2026-08",
        )
        # UTC 2026-08-31 15:00 → JST 2026-09-01 00:00
        self.assertEqual(
            resolve_run_month(
                datetime(2026, 8, 31, 15, 0, tzinfo=timezone.utc)
            ),
            "2026-09",
        )


if __name__ == "__main__":
    unittest.main()
