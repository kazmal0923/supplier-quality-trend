"""単一仕入先・仕入先グループの月別集計。"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Iterable

from supplier_quality_trend.aliases import normalize_supplier_name
from supplier_quality_trend.models import (
    AggregationResult,
    AliasRule,
    DashboardEntity,
    EntityMonth,
    NormalizedRecord,
    WarningItem,
)
from supplier_quality_trend.validation import resolve_run_month

TARGET_RATE = Decimal("0.01")
ABNORMAL_RATE = Decimal("1")


def supplier_id_sort_key(supplier_id: str) -> tuple[int, int, str]:
    """仕入先IDの表示・出力順キー。数字のみは数値昇順、それ以外は後段で文字列順。"""

    trimmed = supplier_id.strip()
    if trimmed.isdigit():
        return (0, int(trimmed), "")
    return (1, 0, trimmed)


def _month_index(value: str) -> int:
    year, month = (int(part) for part in value.split("-"))
    return year * 12 + month - 1


def _month_from_index(value: int) -> str:
    year, month_index = divmod(value, 12)
    return f"{year:04d}-{month_index + 1:02d}"


def month_sequence(start: str, end: str) -> tuple[str, ...]:
    """開始月から終了月までを両端含みで返す。"""

    start_index = _month_index(start)
    end_index = _month_index(end)
    if start_index > end_index:
        raise ValueError("Start month must not be after end month")
    return tuple(
        _month_from_index(index)
        for index in range(start_index, end_index + 1)
    )


def default_start_month(latest_month: str) -> str:
    """最新月を含む13か月の開始月を返す。"""

    return _month_from_index(_month_index(latest_month) - 12)


def _deduplicate_records(
    records: Iterable[NormalizedRecord],
) -> tuple[tuple[NormalizedRecord, ...], tuple[WarningItem, ...]]:
    grouped: dict[tuple[str, str], list[NormalizedRecord]] = defaultdict(list)
    for record in records:
        grouped[(record.target_month, record.supplier_id)].append(record)

    combined: list[NormalizedRecord] = []
    warnings: list[WarningItem] = []
    for (target_month, supplier_id), duplicates in grouped.items():
        first = duplicates[0]
        return_quantity = sum(
            (item.return_quantity for item in duplicates),
            Decimal(0),
        )
        shipment_quantity = sum(
            (item.shipment_quantity for item in duplicates),
            Decimal(0),
        )
        combined.append(
            NormalizedRecord(
                target_month=target_month,
                supplier_id=supplier_id,
                historical_name=first.historical_name,
                current_name=first.current_name,
                category=first.category,
                return_quantity=return_quantity,
                shipment_quantity=shipment_quantity,
                source_rate=first.source_rate,
                master_registered=first.master_registered,
            )
        )
        if len(duplicates) > 1:
            warnings.append(
                WarningItem(
                    code="DUPLICATE_SUPPLIER_MONTH",
                    message="Duplicate rows were combined",
                    target_month=target_month,
                    supplier_id=supplier_id,
                )
            )
        if (
            shipment_quantity > 0
            and return_quantity / shipment_quantity >= ABNORMAL_RATE
        ):
            warnings.append(
                WarningItem(
                    code="RATE_100_PERCENT_OR_MORE",
                    message="Defective rate is 100 percent or more",
                    target_month=target_month,
                    supplier_id=supplier_id,
                )
            )
    return tuple(combined), tuple(warnings)


def _entity_months(
    records: tuple[NormalizedRecord, ...],
    supplier_ids: tuple[str, ...],
    months: tuple[str, ...],
    warnings: tuple[WarningItem, ...],
    *,
    in_progress_month: str | None,
) -> tuple[EntityMonth, ...]:
    selected = [
        record for record in records if record.supplier_id in supplier_ids
    ]
    by_month: dict[str, list[NormalizedRecord]] = defaultdict(list)
    for record in selected:
        by_month[record.target_month].append(record)

    output: list[EntityMonth] = []
    for target_month in months:
        monthly_records = by_month.get(target_month, [])
        warning_codes = sorted(
            {
                warning.code
                for warning in warnings
                if warning.target_month == target_month
                and (
                    warning.supplier_id is None
                    or warning.supplier_id in supplier_ids
                )
            }
        )
        statuses: list[str] = []
        if not monthly_records:
            statuses.append("missing")
            if target_month == in_progress_month:
                statuses.append("in_progress")
            output.append(
                EntityMonth(
                    target_month=target_month,
                    return_quantity=Decimal(0),
                    shipment_quantity=Decimal(0),
                    defective_rate=None,
                    statuses=tuple(statuses),
                    warning_codes=tuple(sorted(set(warning_codes + ["MISSING_MONTH"]))),
                )
            )
            continue

        return_quantity = sum(
            (record.return_quantity for record in monthly_records),
            Decimal(0),
        )
        shipment_quantity = sum(
            (record.shipment_quantity for record in monthly_records),
            Decimal(0),
        )
        defective_rate = (
            None
            if shipment_quantity == 0
            else return_quantity / shipment_quantity
        )
        if shipment_quantity == 0:
            statuses.append("zero_shipment")
        if defective_rate is not None and defective_rate >= TARGET_RATE:
            statuses.append("target_exceeded")
        if defective_rate is not None and defective_rate >= ABNORMAL_RATE:
            statuses.append("abnormal")
        if target_month == in_progress_month:
            statuses.append("in_progress")

        output.append(
            EntityMonth(
                target_month=target_month,
                return_quantity=return_quantity,
                shipment_quantity=shipment_quantity,
                defective_rate=defective_rate,
                statuses=tuple(statuses),
                warning_codes=tuple(warning_codes),
            )
        )
    return tuple(output)


def aggregate_dashboard(
    records: Iterable[NormalizedRecord],
    alias_rules: dict[str, AliasRule],
    warnings: Iterable[WarningItem] = (),
    *,
    input_months: Iterable[str] = (),
    generated_at: datetime | None = None,
) -> AggregationResult:
    """単一仕入先・グループの画面用月別集計を生成する。"""

    deduplicated, duplicate_warnings = _deduplicate_records(records)
    all_warnings = tuple(warnings) + duplicate_warnings
    record_months = sorted(
        {record.target_month for record in deduplicated}
    )
    if not record_months:
        raise ValueError("No valid data months")
    latest_month = record_months[-1]
    data_months = sorted(set(record_months) | set(input_months))
    initial_start = default_start_month(latest_month)
    all_months = month_sequence(
        min(data_months[0], initial_start),
        latest_month,
    )
    timestamp = generated_at or datetime.now(timezone.utc)
    run_month = resolve_run_month(timestamp)
    in_progress_month = latest_month if latest_month == run_month else None

    records_by_supplier: dict[str, list[NormalizedRecord]] = defaultdict(list)
    for record in deduplicated:
        records_by_supplier[record.supplier_id].append(record)

    entities: list[DashboardEntity] = []
    for supplier_id, supplier_records in sorted(
        records_by_supplier.items(),
        key=lambda item: supplier_id_sort_key(item[0]),
    ):
        latest_record = max(supplier_records, key=lambda item: item.target_month)
        entities.append(
            DashboardEntity(
                entity_id=f"supplier:{supplier_id}",
                entity_type="supplier",
                display_name=latest_record.current_name,
                category=latest_record.category,
                supplier_ids=(supplier_id,),
                supplier_names=(latest_record.current_name,),
                months=_entity_months(
                    deduplicated,
                    (supplier_id,),
                    all_months,
                    all_warnings,
                    in_progress_month=in_progress_month,
                ),
            )
        )

    group_members: dict[str, set[str]] = defaultdict(set)
    group_names: dict[str, str] = {}
    canonical_names = {
        rule.canonical_group_name for rule in alias_rules.values()
    }
    for supplier_id, supplier_records in records_by_supplier.items():
        latest_record = max(supplier_records, key=lambda item: item.target_month)
        current_name = normalize_supplier_name(latest_record.current_name)
        alias = alias_rules.get(current_name)
        if alias is not None:
            key = f"alias:{alias.canonical_group_name}"
            group_names[key] = alias.canonical_group_name
        elif current_name in canonical_names:
            key = f"alias:{current_name}"
            group_names[key] = current_name
        else:
            key = f"auto:{latest_record.category}:{current_name}"
            group_names[key] = current_name
        group_members[key].add(supplier_id)

    for key in sorted(group_members):
        supplier_ids = tuple(
            sorted(group_members[key], key=supplier_id_sort_key)
        )
        categories = sorted(
            {
                record.category
                for record in deduplicated
                if record.supplier_id in supplier_ids and record.category
            }
        )
        supplier_names = tuple(
            sorted(
                {
                    max(
                        records_by_supplier[supplier_id],
                        key=lambda item: item.target_month,
                    ).current_name
                    for supplier_id in supplier_ids
                }
            )
        )
        entities.append(
            DashboardEntity(
                entity_id=f"group:{key}",
                entity_type="group",
                display_name=group_names[key],
                category="／".join(categories),
                supplier_ids=supplier_ids,
                supplier_names=supplier_names,
                months=_entity_months(
                    deduplicated,
                    supplier_ids,
                    all_months,
                    all_warnings,
                    in_progress_month=in_progress_month,
                ),
            )
        )

    return AggregationResult(
        generated_at=timestamp,
        latest_data_month=latest_month,
        default_start_month=default_start_month(latest_month),
        default_end_month=latest_month,
        entities=tuple(entities),
        warnings=all_warnings,
    )
