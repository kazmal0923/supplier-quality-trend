"""Supplier Quality Trend batch entry point."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from supplier_quality_trend.lock import exclusive_run_lock
from supplier_quality_trend.output import (
    atomic_write_json,
    failure_status_document,
)
from supplier_quality_trend.pipeline import run_pipeline
from supplier_quality_trend.validation import ValidationError

_SAFE_ERROR_DETAILS = {
    "AliasError": "Alias validation failed",
    "AlreadyRunningError": "Batch is already running",
    "MonthlyCsvError": "Monthly CSV validation failed",
    "SettingsError": "Settings validation failed",
    "SupplierMasterError": "Supplier master validation failed",
    "ValidationError": "Monthly value validation failed",
}


def _safe_error_detail(error: Exception) -> str:
    return _SAFE_ERROR_DETAILS.get(
        type(error).__name__,
        "Unexpected pipeline failure",
    )


def _record_failure(root: Path, error: Exception, generated_at: str) -> None:
    logs_directory = root / "logs"
    logs_directory.mkdir(parents=True, exist_ok=True)
    log_path = logs_directory / "error.log"
    with log_path.open("a", encoding="utf-8", newline="\n") as log_file:
        log_file.write(
            f"{generated_at} ERROR {type(error).__name__} "
            f"{_safe_error_detail(error)}\n"
        )
        if isinstance(error, ValidationError):
            for warning in error.warnings:
                details = {
                    "code": warning.code,
                    "file": warning.source_file,
                    "line": warning.line_number,
                    "column": warning.column_name,
                    "raw": warning.raw_value,
                }
                log_file.write(
                    f"{generated_at} WARNING "
                    f"{json.dumps(details, ensure_ascii=True)}\n"
                )
    atomic_write_json(
        root / "web" / "data" / "update-status.json",
        failure_status_document(generated_at),
    )


def main() -> int:
    """バッチを実行し、成功0・失敗1を返す。"""

    root = Path(__file__).resolve().parent
    generated_at = datetime.now(timezone.utc).isoformat()
    try:
        with exclusive_run_lock(root):
            run_pipeline(root)
    except Exception as error:  # エントリーポイントでログへ集約する。
        try:
            _record_failure(root, error, generated_at)
        except Exception:
            pass
        print("ERROR")
        return 1

    print("SUCCESS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
