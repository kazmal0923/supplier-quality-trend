"""JSON生成と原子的置換のテスト。"""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import supplier_quality_trend.output as output_module
from supplier_quality_trend.aggregation import aggregate_dashboard
from supplier_quality_trend.models import NormalizedRecord, WarningItem
from supplier_quality_trend.output import dashboard_document, write_success_outputs


class OutputTest(unittest.TestCase):
    def _result(self):
        return aggregate_dashboard(
            (
                NormalizedRecord(
                    target_month="2026-01",
                    supplier_id="S001",
                    historical_name="架空仕入先A",
                    current_name="架空仕入先A",
                    category="国内仕入れ",
                    return_quantity=Decimal("1"),
                    shipment_quantity=Decimal("100"),
                    source_rate=Decimal("0.01"),
                    master_registered=True,
                ),
            ),
            {},
            generated_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
        )

    def test_writes_valid_dashboard_and_status_json(self) -> None:
        result = self._result()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_success_outputs(root, result)
            dashboard = json.loads(
                (root / "web/data/dashboard-data.json").read_text(
                    encoding="utf-8"
                )
            )
            status = json.loads(
                (root / "web/data/update-status.json").read_text(
                    encoding="utf-8"
                )
            )
        self.assertEqual(dashboard["schemaVersion"], 1)
        self.assertEqual(dashboard["entities"][0]["supplierIds"], ["S001"])
        self.assertEqual(
            dashboard["entities"][0]["supplierNames"],
            ["架空仕入先A"],
        )
        self.assertEqual(dashboard["warningCount"], 12)
        self.assertEqual(status["status"], "success")
        self.assertEqual(status["warningCount"], 12)

    def test_warning_details_use_filename_without_absolute_path(self) -> None:
        result = aggregate_dashboard(
            (
                NormalizedRecord(
                    target_month="2026-01",
                    supplier_id="S001",
                    historical_name="架空仕入先A",
                    current_name="架空仕入先A",
                    category="国内仕入れ",
                    return_quantity=Decimal("1"),
                    shipment_quantity=Decimal("100"),
                    source_rate=None,
                    master_registered=True,
                ),
            ),
            {},
            (
                WarningItem(
                    code="INVALID_HENPIN_SU",
                    message="HENPIN_SU invalid row was excluded",
                    target_month="2026-01",
                    supplier_id="S001",
                    source_file="2026年01月.csv",
                    line_number=2,
                    column_name="HENPIN_SU",
                    raw_value="invalid",
                ),
            ),
            generated_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
        )
        warning = dashboard_document(result)["warnings"][0]
        self.assertEqual(warning["sourceFile"], "2026年01月.csv")
        self.assertEqual(warning["lineNumber"], 2)
        self.assertEqual(warning["columnName"], "HENPIN_SU")
        self.assertEqual(warning["rawValue"], "invalid")

    def test_second_output_failure_restores_both_previous_files(self) -> None:
        result = self._result()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data = root / "web/data"
            data.mkdir(parents=True)
            dashboard_path = data / "dashboard-data.json"
            status_path = data / "update-status.json"
            dashboard_path.write_bytes(b'{"old":"dashboard"}\n')
            status_path.write_bytes(b'{"old":"status"}\n')
            original_replace = output_module.os.replace
            calls = 0

            def fail_second_replace(source, destination):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("simulated status replace failure")
                return original_replace(source, destination)

            with patch.object(
                output_module.os,
                "replace",
                side_effect=fail_second_replace,
            ):
                with self.assertRaises(OSError):
                    write_success_outputs(root, result)

            self.assertEqual(
                dashboard_path.read_bytes(),
                b'{"old":"dashboard"}\n',
            )
            self.assertEqual(status_path.read_bytes(), b'{"old":"status"}\n')


if __name__ == "__main__":
    unittest.main()
