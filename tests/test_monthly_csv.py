"""月次不良率CSV読込のテスト。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from supplier_quality_trend.monthly_csv import (
    MonthlyCsvError,
    discover_monthly_csvs,
    parse_target_month,
    read_monthly_csv,
)

HEADER = (
    "SHIIRESAKI_ID,SHIIRESAKI_NM,HENPIN_SU,"
    "SYUKKA_SU,DEFECTIVE_RATE"
)
ROW = "S001,架空仕入先A,1,100,0.01"


class MonthlyCsvTest(unittest.TestCase):
    def _write_csv(
        self,
        directory: Path,
        *,
        filename: str = "2026年01月.csv",
        encoding: str = "utf-8",
        newline: str = "\n",
        header: str = HEADER,
        row: str = ROW,
    ) -> Path:
        path = directory / filename
        path.write_bytes(
            f"{header}{newline}{row}{newline}".encode(encoding)
        )
        return path

    def test_parse_target_month(self) -> None:
        self.assertEqual(parse_target_month("2026年01月.csv"), "2026-01")

    def test_invalid_filename_stops_processing(self) -> None:
        with self.assertRaises(MonthlyCsvError):
            parse_target_month("2026-01.csv")

    def test_reads_bom_and_newline_variants(self) -> None:
        variants = (
            ("utf-8", "\n"),
            ("utf-8", "\r\n"),
            ("utf-8-sig", "\n"),
            ("utf-8-sig", "\r\n"),
        )
        for encoding, newline in variants:
            with self.subTest(encoding=encoding, newline=repr(newline)):
                with tempfile.TemporaryDirectory() as temporary:
                    path = self._write_csv(
                        Path(temporary),
                        encoding=encoding,
                        newline=newline,
                    )
                    loaded = read_monthly_csv(path)
                    self.assertEqual(loaded.target_month, "2026-01")
                    self.assertEqual(loaded.rows[0]["SHIIRESAKI_ID"], "S001")

    def test_missing_required_column_stops_processing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = self._write_csv(
                Path(temporary),
                header="SHIIRESAKI_ID,SHIIRESAKI_NM,HENPIN_SU,SYUKKA_SU",
            )
            with self.assertRaisesRegex(
                MonthlyCsvError, "DEFECTIVE_RATE"
            ):
                read_monthly_csv(path)

    def test_short_row_converts_missing_items_to_empty_strings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = self._write_csv(
                Path(temporary),
                row="S001,架空仕入先A,1",
            )
            loaded = read_monthly_csv(path)
        self.assertEqual(loaded.rows[0]["HENPIN_SU"], "1")
        self.assertEqual(loaded.rows[0]["SYUKKA_SU"], "")
        self.assertEqual(loaded.rows[0]["DEFECTIVE_RATE"], "")

    def test_discovers_multiple_months_in_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self._write_csv(directory, filename="2026年02月.csv")
            self._write_csv(directory, filename="2026年01月.csv")
            loaded = discover_monthly_csvs(directory)
            self.assertEqual(
                [item.target_month for item in loaded],
                ["2026-01", "2026-02"],
            )


if __name__ == "__main__":
    unittest.main()
