"""画面用JSONの生成と原子的置換。"""

from __future__ import annotations

import json
import os
import tempfile
from decimal import Decimal
from pathlib import Path
from typing import Any

from supplier_quality_trend.models import AggregationResult, WarningItem

SCHEMA_VERSION = 1


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")


def _warning_dict(warning: WarningItem) -> dict[str, Any]:
    return {
        "code": warning.code,
        "message": warning.message,
        "targetMonth": warning.target_month,
        "supplierId": warning.supplier_id,
        "sourceFile": warning.source_file,
        "lineNumber": warning.line_number,
        "columnName": warning.column_name,
        "rawValue": warning.raw_value,
    }


def _warning_count(result: AggregationResult) -> int:
    missing_months = sum(
        1
        for entity in result.entities
        if entity.entity_type == "supplier"
        for month in entity.months
        if "MISSING_MONTH" in month.warning_codes
    )
    return len(result.warnings) + missing_months


def dashboard_document(result: AggregationResult) -> dict[str, Any]:
    """集計結果を公開可能なJSON文書へ変換する。"""

    return {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": result.generated_at.isoformat(),
        "latestDataMonth": result.latest_data_month,
        "defaultPeriod": {
            "startMonth": result.default_start_month,
            "endMonth": result.default_end_month,
        },
        "warningCount": _warning_count(result),
        "entities": [
            {
                "entityId": entity.entity_id,
                "entityType": entity.entity_type,
                "displayName": entity.display_name,
                "category": entity.category,
                "supplierIds": list(entity.supplier_ids),
                "supplierNames": list(entity.supplier_names),
                "months": [
                    {
                        "targetMonth": month.target_month,
                        "returnQuantity": _decimal_text(month.return_quantity),
                        "shipmentQuantity": _decimal_text(
                            month.shipment_quantity
                        ),
                        "defectiveRate": (
                            None
                            if month.defective_rate is None
                            else _decimal_text(month.defective_rate)
                        ),
                        "statuses": list(month.statuses),
                        "warningCodes": list(month.warning_codes),
                    }
                    for month in entity.months
                ],
            }
            for entity in result.entities
        ],
        "warnings": [_warning_dict(warning) for warning in result.warnings],
    }


def success_status_document(result: AggregationResult) -> dict[str, Any]:
    """正常更新状態をJSON文書へ変換する。"""

    return {
        "schemaVersion": SCHEMA_VERSION,
        "status": "success",
        "generatedAt": result.generated_at.isoformat(),
        "latestDataMonth": result.latest_data_month,
        "warningCount": _warning_count(result),
    }


def failure_status_document(generated_at: str) -> dict[str, Any]:
    """失敗状態を機密情報なしで表す。"""

    return {
        "schemaVersion": SCHEMA_VERSION,
        "status": "failure",
        "generatedAt": generated_at,
        "message": "Data update failed. Previous dashboard data was kept.",
    }


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def atomic_write_json(path: Path, document: dict[str, Any]) -> None:
    """同一ディレクトリの一時ファイルからJSONを置換する。"""

    content = (
        json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")
    _atomic_write_bytes(path, content)


def write_success_outputs(root: Path, result: AggregationResult) -> None:
    """ダッシュボードデータと正常更新状態を出力する。"""

    data_directory = root / "web" / "data"
    dashboard_path = data_directory / "dashboard-data.json"
    status_path = data_directory / "update-status.json"

    dashboard_document_value = dashboard_document(result)
    status_document_value = success_status_document(result)

    # 置換前に両方の文書がJSON化可能であることを確認する。
    json.dumps(dashboard_document_value, ensure_ascii=False)
    json.dumps(status_document_value, ensure_ascii=False)

    previous_dashboard = (
        dashboard_path.read_bytes() if dashboard_path.exists() else None
    )
    previous_status = status_path.read_bytes() if status_path.exists() else None
    try:
        atomic_write_json(dashboard_path, dashboard_document_value)
        atomic_write_json(status_path, status_document_value)
    except Exception:
        if previous_dashboard is None:
            dashboard_path.unlink(missing_ok=True)
        else:
            _atomic_write_bytes(dashboard_path, previous_dashboard)
        if previous_status is None:
            status_path.unlink(missing_ok=True)
        else:
            _atomic_write_bytes(status_path, previous_status)
        raise
