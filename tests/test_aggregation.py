"""月別・期間・グループ集計のテスト。"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from decimal import Decimal

from supplier_quality_trend.aggregation import aggregate_dashboard
from supplier_quality_trend.models import AliasRule, NormalizedRecord
from supplier_quality_trend.periods import (
    find_month,
    previous_year_month,
    summarize_period,
)


def _record(
    month: str,
    supplier_id: str,
    name: str,
    returns: str,
    shipments: str,
    *,
    category: str = "国内仕入れ",
    source_rate: str | None = None,
) -> NormalizedRecord:
    return NormalizedRecord(
        target_month=month,
        supplier_id=supplier_id,
        historical_name=name,
        current_name=name,
        category=category,
        return_quantity=Decimal(returns),
        shipment_quantity=Decimal(shipments),
        source_rate=None if source_rate is None else Decimal(source_rate),
        master_registered=True,
    )


class AggregationTest(unittest.TestCase):
    def test_source_defective_rate_does_not_affect_aggregation(self) -> None:
        result = aggregate_dashboard(
            (
                _record(
                    "2026-01",
                    "S001",
                    "架空仕入先A",
                    "1",
                    "100",
                    source_rate="999",
                ),
            ),
            {},
            generated_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
        )
        entity = next(
            item for item in result.entities
            if item.entity_id == "supplier:S001"
        )
        self.assertEqual(entity.months[-1].defective_rate, Decimal("0.01"))

    def test_period_rate_uses_quantity_totals_not_monthly_average(self) -> None:
        result = aggregate_dashboard(
            (
                _record("2026-01", "S001", "架空仕入先A", "1", "10"),
                _record("2026-02", "S001", "架空仕入先A", "0", "90"),
            ),
            {},
            generated_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
        )
        entity = next(
            item for item in result.entities
            if item.entity_id == "supplier:S001"
        )
        summary = summarize_period(entity.months, "2026-01", "2026-02")
        self.assertEqual(summary.defective_rate, Decimal("0.01"))

    def test_duplicate_rows_are_combined_with_warning(self) -> None:
        result = aggregate_dashboard(
            (
                _record("2026-01", "S001", "架空仕入先A", "1", "10"),
                _record("2026-01", "S001", "架空仕入先A", "2", "20"),
            ),
            {},
            generated_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
        )
        entity = next(
            item for item in result.entities
            if item.entity_id == "supplier:S001"
        )
        january = next(
            item for item in entity.months if item.target_month == "2026-01"
        )
        self.assertEqual(january.return_quantity, Decimal("3"))
        self.assertEqual(january.shipment_quantity, Decimal("30"))
        self.assertIn(
            "DUPLICATE_SUPPLIER_MONTH",
            {warning.code for warning in result.warnings},
        )

    def test_same_name_and_category_are_automatically_grouped(self) -> None:
        result = aggregate_dashboard(
            (
                _record("2026-01", "S001", "同一架空名", "1", "10"),
                _record("2026-01", "S002", "同一架空名", "1", "90"),
            ),
            {},
            generated_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
        )
        group = next(
            item for item in result.entities
            if item.entity_type == "group"
            and item.display_name == "同一架空名"
        )
        january = next(
            item for item in group.months if item.target_month == "2026-01"
        )
        self.assertEqual(group.supplier_ids, ("S001", "S002"))
        self.assertEqual(january.defective_rate, Decimal("0.02"))

    def test_cross_category_group_requires_explicit_alias(self) -> None:
        records = (
            _record(
                "2026-01",
                "S001",
                "架空名A",
                "1",
                "10",
                category="国内仕入れ",
            ),
            _record(
                "2026-01",
                "S002",
                "架空名B",
                "1",
                "90",
                category="海外仕入れ",
            ),
        )
        aliases = {
            "架空名B": AliasRule("架空名A", "架空名B", ""),
        }
        result = aggregate_dashboard(
            records,
            aliases,
            generated_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
        )
        group = next(
            item for item in result.entities
            if item.entity_type == "group"
            and item.display_name == "架空名A"
        )
        self.assertEqual(group.category, "国内仕入れ／海外仕入れ")
        self.assertEqual(group.supplier_ids, ("S001", "S002"))
        self.assertEqual(group.supplier_names, ("架空名A", "架空名B"))

    def test_latest_thirteen_months_include_missing_months(self) -> None:
        result = aggregate_dashboard(
            (_record("2026-02", "S001", "架空仕入先A", "1", "100"),),
            {},
            generated_at=datetime(2026, 2, 15, tzinfo=timezone.utc),
        )
        entity = next(
            item for item in result.entities
            if item.entity_id == "supplier:S001"
        )
        self.assertEqual(result.default_start_month, "2025-02")
        self.assertEqual(len(entity.months), 13)
        self.assertIn("in_progress", entity.months[-1].statuses)
        self.assertIn("missing", entity.months[0].statuses)

    def test_zero_shipment_rate_is_none(self) -> None:
        result = aggregate_dashboard(
            (_record("2026-01", "S001", "架空仕入先A", "1", "0"),),
            {},
            generated_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
        )
        entity = next(
            item for item in result.entities
            if item.entity_id == "supplier:S001"
        )
        january = entity.months[-1]
        self.assertEqual(january.return_quantity, Decimal("1"))
        self.assertEqual(january.shipment_quantity, Decimal("0"))
        self.assertIsNone(january.defective_rate)
        self.assertIn("zero_shipment", january.statuses)

    def test_zero_shipment_group_keeps_quantity_and_rate_none(self) -> None:
        result = aggregate_dashboard(
            (
                _record("2026-01", "S001", "同一架空名", "1", "0"),
                _record("2026-01", "S002", "同一架空名", "2", "0"),
            ),
            {},
            generated_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
        )
        group = next(
            item for item in result.entities
            if item.entity_type == "group"
        )
        january = group.months[-1]
        self.assertEqual(january.return_quantity, Decimal("3"))
        self.assertEqual(january.shipment_quantity, Decimal("0"))
        self.assertIsNone(january.defective_rate)

    def test_zero_returns_target_boundary_and_abnormal_value(self) -> None:
        result = aggregate_dashboard(
            (
                _record("2025-12", "S001", "架空仕入先A", "0", "100"),
                _record("2026-01", "S001", "架空仕入先A", "1", "100"),
                _record("2026-02", "S001", "架空仕入先A", "101", "100"),
            ),
            {},
            generated_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
        )
        entity = next(
            item for item in result.entities
            if item.entity_id == "supplier:S001"
        )
        zero_return = find_month(entity, "2025-12")
        target_boundary = find_month(entity, "2026-01")
        abnormal = find_month(entity, "2026-02")
        self.assertEqual(zero_return.defective_rate, Decimal(0))
        self.assertNotIn("target_exceeded", zero_return.statuses)
        self.assertIn("target_exceeded", target_boundary.statuses)
        self.assertIn("abnormal", abnormal.statuses)
        self.assertIn(
            "RATE_100_PERCENT_OR_MORE",
            {warning.code for warning in result.warnings},
        )

    def test_previous_year_month_without_data_is_missing(self) -> None:
        result = aggregate_dashboard(
            (_record("2026-02", "S001", "架空仕入先A", "1", "100"),),
            {},
            generated_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
        )
        entity = next(
            item for item in result.entities
            if item.entity_id == "supplier:S001"
        )
        previous = find_month(
            entity,
            previous_year_month(result.latest_data_month),
        )
        self.assertIsNotNone(previous)
        self.assertIn("missing", previous.statuses)

    def test_empty_latest_input_month_without_records_fails(self) -> None:
        with self.assertRaises(ValueError):
            aggregate_dashboard(
                (),
                {},
                input_months=("2026-02",),
                generated_at=datetime(2026, 2, 15, tzinfo=timezone.utc),
            )

    def test_latest_data_month_uses_valid_records_only(self) -> None:
        result = aggregate_dashboard(
            (_record("2026-01", "S001", "架空仕入先A", "1", "100"),),
            {},
            input_months=("2026-01", "2026-02"),
            generated_at=datetime(2026, 2, 15, tzinfo=timezone.utc),
        )
        self.assertEqual(result.latest_data_month, "2026-01")
        entity = next(
            item for item in result.entities
            if item.entity_id == "supplier:S001"
        )
        self.assertEqual(entity.months[-1].target_month, "2026-01")
        self.assertNotIn(
            "in_progress",
            entity.months[-1].statuses,
        )

    def test_current_month_with_data_is_in_progress(self) -> None:
        result = aggregate_dashboard(
            (
                _record("2026-01", "S001", "架空仕入先A", "1", "100"),
                _record("2026-02", "S001", "架空仕入先A", "2", "100"),
            ),
            {},
            generated_at=datetime(2026, 2, 15, tzinfo=timezone.utc),
        )
        entity = next(
            item for item in result.entities
            if item.entity_id == "supplier:S001"
        )
        current = find_month(entity, "2026-02")
        self.assertIn("in_progress", current.statuses)


if __name__ == "__main__":
    unittest.main()
