"""期間全体と前年同月の集計補助。"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from supplier_quality_trend.models import DashboardEntity, EntityMonth


@dataclass(frozen=True)
class PeriodSummary:
    """選択期間の数量合計と現行不良率。"""

    return_quantity: Decimal
    shipment_quantity: Decimal
    defective_rate: Decimal | None


def summarize_period(
    months: tuple[EntityMonth, ...],
    start_month: str,
    end_month: str,
) -> PeriodSummary:
    """月別率を平均せず、選択期間の数量合計から再計算する。"""

    selected = [
        item
        for item in months
        if start_month <= item.target_month <= end_month
        and "missing" not in item.statuses
    ]
    return_quantity = sum(
        (item.return_quantity for item in selected),
        Decimal(0),
    )
    shipment_quantity = sum(
        (item.shipment_quantity for item in selected),
        Decimal(0),
    )
    return PeriodSummary(
        return_quantity=return_quantity,
        shipment_quantity=shipment_quantity,
        defective_rate=(
            None
            if shipment_quantity == 0
            else return_quantity / shipment_quantity
        ),
    )


def find_month(
    entity: DashboardEntity,
    target_month: str,
) -> EntityMonth | None:
    """表示単位から指定月を取得する。"""

    return next(
        (item for item in entity.months if item.target_month == target_month),
        None,
    )


def previous_year_month(target_month: str) -> str:
    """前年同月を返す。"""

    year, month = target_month.split("-")
    return f"{int(year) - 1:04d}-{month}"
