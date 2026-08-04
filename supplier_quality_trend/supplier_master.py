"""仕入先マスタの読込と月次レコードへの結合。"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Final, Iterable

from supplier_quality_trend.models import (
    MonthlyRecord,
    NormalizedRecord,
    SupplierMasterEntry,
    WarningItem,
)

MASTER_COLUMNS: Final[tuple[str, ...]] = (
    "DISPLAY_NM_1",
    "SHIIRESAKI_ID",
    "SHIIRESAKI_NM1",
)


class SupplierMasterError(ValueError):
    """仕入先マスタの仕様違反。"""


def read_supplier_master(path: Path) -> dict[str, SupplierMasterEntry]:
    """CP932の仕入先マスタをID辞書として読み込む。"""

    if path.name != "仕入先マスタ_絞り込み無し.csv":
        raise SupplierMasterError(f"Invalid supplier master filename: {path.name}")

    try:
        with path.open("r", encoding="cp932", newline="") as source:
            reader = csv.DictReader(source, delimiter=",")
            fieldnames = tuple(reader.fieldnames or ())
            missing = [column for column in MASTER_COLUMNS if column not in fieldnames]
            if missing:
                raise SupplierMasterError(
                    f"Missing supplier master columns: {', '.join(missing)}"
                )

            entries: dict[str, SupplierMasterEntry] = {}
            for row in reader:
                supplier_id = (row.get("SHIIRESAKI_ID") or "").strip()
                if not supplier_id:
                    raise SupplierMasterError("Supplier master ID is empty")
                if supplier_id in entries:
                    raise SupplierMasterError(
                        f"Duplicate supplier master ID: {supplier_id}"
                    )
                entries[supplier_id] = SupplierMasterEntry(
                    category=(row.get("DISPLAY_NM_1") or "").strip(),
                    supplier_id=supplier_id,
                    current_name=(row.get("SHIIRESAKI_NM1") or "").strip(),
                )
    except UnicodeDecodeError as exc:
        raise SupplierMasterError("Supplier master is not CP932") from exc
    except OSError as exc:
        raise SupplierMasterError(f"Cannot read supplier master: {path}") from exc

    return entries


def join_supplier_master(
    records: Iterable[MonthlyRecord],
    master: dict[str, SupplierMasterEntry],
) -> tuple[tuple[NormalizedRecord, ...], tuple[WarningItem, ...]]:
    """現在名称を付加し、未登録IDは月次名称で保持する。"""

    normalized: list[NormalizedRecord] = []
    warnings: list[WarningItem] = []
    for record in records:
        entry = master.get(record.supplier_id)
        if entry is None:
            normalized.append(
                NormalizedRecord(
                    target_month=record.target_month,
                    supplier_id=record.supplier_id,
                    historical_name=record.historical_name,
                    current_name=record.historical_name,
                    category="",
                    return_quantity=record.return_quantity,
                    shipment_quantity=record.shipment_quantity,
                    source_rate=record.source_rate,
                    master_registered=False,
                )
            )
            warnings.append(
                WarningItem(
                    code="MASTER_NOT_FOUND",
                    message="Supplier ID is not registered in master",
                    target_month=record.target_month,
                    supplier_id=record.supplier_id,
                )
            )
            continue

        normalized.append(
            NormalizedRecord(
                target_month=record.target_month,
                supplier_id=record.supplier_id,
                historical_name=record.historical_name,
                current_name=entry.current_name,
                category=entry.category,
                return_quantity=record.return_quantity,
                shipment_quantity=record.shipment_quantity,
                source_rate=record.source_rate,
                master_registered=True,
            )
        )
        if record.historical_name.strip() != entry.current_name.strip():
            warnings.append(
                WarningItem(
                    code="SUPPLIER_NAME_CHANGED",
                    message="Monthly and current supplier names differ",
                    target_month=record.target_month,
                    supplier_id=record.supplier_id,
                )
            )

    return tuple(normalized), tuple(warnings)
