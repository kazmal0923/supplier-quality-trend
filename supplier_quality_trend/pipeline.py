"""MVPバッチ処理のオーケストレーション。"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from supplier_quality_trend.aggregation import aggregate_dashboard
from supplier_quality_trend.aliases import read_alias_rules
from supplier_quality_trend.config import load_settings
from supplier_quality_trend.monthly_csv import discover_monthly_csvs
from supplier_quality_trend.output import write_success_outputs
from supplier_quality_trend.supplier_master import (
    join_supplier_master,
    read_supplier_master,
)
from supplier_quality_trend.validation import (
    parse_monthly_records,
    resolve_run_month,
)


def run_pipeline(
    root: Path,
    *,
    generated_at: datetime | None = None,
) -> None:
    """入力から画面用JSON生成までを実行する。"""

    timestamp = generated_at or datetime.now(timezone.utc)
    run_month = resolve_run_month(timestamp)
    settings = load_settings(root / "config" / "settings.json")
    monthly_files = discover_monthly_csvs(settings.monthly_csv_directory)
    monthly_records, input_warnings = parse_monthly_records(
        monthly_files,
        run_month=run_month,
    )
    supplier_master = read_supplier_master(settings.supplier_master_file)
    normalized_records, master_warnings = join_supplier_master(
        monthly_records,
        supplier_master,
    )
    alias_rules = read_alias_rules(
        root / "config" / "supplier-name-aliases.csv"
    )
    result = aggregate_dashboard(
        normalized_records,
        alias_rules,
        input_warnings + master_warnings,
        input_months=tuple(
            sorted({record.target_month for record in monthly_records})
        ),
        generated_at=timestamp,
    )
    write_success_outputs(root, result)
