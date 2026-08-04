"""アプリ内で共有するデータモデル。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True)
class WarningItem:
    """処理を継続できるデータ警告。"""

    code: str
    message: str
    target_month: str | None = None
    supplier_id: str | None = None
    source_file: str | None = None
    line_number: int | None = None
    column_name: str | None = None
    raw_value: str | None = None


@dataclass(frozen=True)
class MonthlyRecord:
    """型変換後の月次レコード。"""

    source_path: Path
    target_month: str
    supplier_id: str
    historical_name: str
    return_quantity: Decimal
    shipment_quantity: Decimal
    source_rate: Decimal | None


@dataclass(frozen=True)
class SupplierMasterEntry:
    """仕入先マスタの1レコード。"""

    category: str
    supplier_id: str
    current_name: str


@dataclass(frozen=True)
class NormalizedRecord:
    """月次データへ現在の仕入先情報を付加したレコード。"""

    target_month: str
    supplier_id: str
    historical_name: str
    current_name: str
    category: str
    return_quantity: Decimal
    shipment_quantity: Decimal
    source_rate: Decimal | None
    master_registered: bool


@dataclass(frozen=True)
class AliasRule:
    """仕入先名エイリアスの有効な定義。"""

    canonical_group_name: str
    alias_supplier_name: str
    note: str


@dataclass(frozen=True)
class EntityMonth:
    """画面へ渡す仕入先・月単位の集計値。"""

    target_month: str
    return_quantity: Decimal
    shipment_quantity: Decimal
    defective_rate: Decimal | None
    statuses: tuple[str, ...]
    warning_codes: tuple[str, ...]


@dataclass(frozen=True)
class DashboardEntity:
    """単一仕入先または仕入先グループの表示単位。"""

    entity_id: str
    entity_type: str
    display_name: str
    category: str
    supplier_ids: tuple[str, ...]
    supplier_names: tuple[str, ...]
    months: tuple[EntityMonth, ...]


@dataclass(frozen=True)
class AggregationResult:
    """全表示単位の集計結果。"""

    generated_at: datetime
    latest_data_month: str
    default_start_month: str
    default_end_month: str
    entities: tuple[DashboardEntity, ...]
    warnings: tuple[WarningItem, ...]
