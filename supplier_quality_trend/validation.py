"""月次行の型変換と警告判定。"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Iterable

from supplier_quality_trend.models import MonthlyRecord, WarningItem
from supplier_quality_trend.monthly_csv import MonthlyCsvData

DEFECTIVE_RATE_TOLERANCE = Decimal("1E-12")


class ValidationError(ValueError):
    """処理を停止する入力値の仕様違反。"""

    def __init__(
        self,
        message: str,
        warnings: tuple[WarningItem, ...] = (),
    ) -> None:
        super().__init__(message)
        self.warnings = warnings


def _parse_non_negative_quantity(
    raw_value: str,
    *,
    field_name: str,
    target_month: str,
    supplier_id: str,
    source_file: str,
    line_number: int,
) -> tuple[Decimal | None, WarningItem | None]:
    try:
        normalized = raw_value.strip()
        if not normalized:
            raise InvalidOperation
        value = Decimal(normalized)
        if not value.is_finite() or value < 0:
            raise InvalidOperation
        return value, None
    except (InvalidOperation, ValueError):
        return (
            None,
            WarningItem(
                code=f"INVALID_{field_name}",
                message=f"{field_name} invalid row was excluded",
                target_month=target_month,
                supplier_id=supplier_id,
                source_file=source_file,
                line_number=line_number,
                column_name=field_name,
                raw_value=raw_value,
            ),
        )


def _parse_source_rate(
    raw_value: str,
    *,
    target_month: str,
    supplier_id: str,
    source_file: str,
    line_number: int,
) -> tuple[Decimal | None, WarningItem | None]:
    try:
        value = Decimal(raw_value.strip())
        if not value.is_finite():
            raise InvalidOperation
        return value, None
    except (InvalidOperation, ValueError):
        return (
            None,
            WarningItem(
                code="INVALID_DEFECTIVE_RATE",
                message="DEFECTIVE_RATE could not be parsed",
                target_month=target_month,
                supplier_id=supplier_id,
                source_file=source_file,
                line_number=line_number,
                column_name="DEFECTIVE_RATE",
                raw_value=raw_value,
            ),
        )


def _rate_warning(
    *,
    monthly_file: MonthlyCsvData,
    row: dict[str, str],
    line_number: int,
    supplier_id: str,
    return_quantity: Decimal,
    shipment_quantity: Decimal,
    source_rate: Decimal | None,
) -> WarningItem | None:
    common = {
        "target_month": monthly_file.target_month,
        "supplier_id": supplier_id,
        "source_file": monthly_file.source_path.name,
        "line_number": line_number,
    }
    if shipment_quantity == 0:
        return WarningItem(
            code="ZERO_SHIPMENT_QUANTITY",
            message="Defective rate cannot be calculated",
            column_name="SYUKKA_SU",
            raw_value=row["SYUKKA_SU"],
            **common,
        )
    calculated_rate = return_quantity / shipment_quantity
    if (
        source_rate is not None
        and abs(calculated_rate - source_rate) > DEFECTIVE_RATE_TOLERANCE
    ):
        return WarningItem(
            code="DEFECTIVE_RATE_MISMATCH",
            message="DEFECTIVE_RATE does not match recalculated rate",
            column_name="DEFECTIVE_RATE",
            raw_value=row["DEFECTIVE_RATE"],
            **common,
        )
    return None


def _parse_monthly_row(
    monthly_file: MonthlyCsvData,
    row: dict[str, str],
    line_number: int,
) -> tuple[MonthlyRecord | None, tuple[WarningItem, ...]]:
    supplier_id = row["SHIIRESAKI_ID"].strip()
    if not supplier_id:
        raise ValidationError(
            f"SHIIRESAKI_ID is empty: {monthly_file.source_path.name}"
        )
    common = {
        "target_month": monthly_file.target_month,
        "supplier_id": supplier_id,
        "source_file": monthly_file.source_path.name,
        "line_number": line_number,
    }
    return_quantity, return_warning = _parse_non_negative_quantity(
        row["HENPIN_SU"],
        field_name="HENPIN_SU",
        **common,
    )
    shipment_quantity, shipment_warning = _parse_non_negative_quantity(
        row["SYUKKA_SU"],
        field_name="SYUKKA_SU",
        **common,
    )
    warnings = tuple(
        warning
        for warning in (return_warning, shipment_warning)
        if warning is not None
    )
    if return_quantity is None or shipment_quantity is None:
        return None, warnings

    source_rate, source_warning = _parse_source_rate(
        row["DEFECTIVE_RATE"],
        **common,
    )
    if source_warning is not None:
        warnings += (source_warning,)
    rate_warning = _rate_warning(
        monthly_file=monthly_file,
        row=row,
        line_number=line_number,
        supplier_id=supplier_id,
        return_quantity=return_quantity,
        shipment_quantity=shipment_quantity,
        source_rate=source_rate,
    )
    if rate_warning is not None:
        warnings += (rate_warning,)
    return (
        MonthlyRecord(
            source_path=monthly_file.source_path,
            target_month=monthly_file.target_month,
            supplier_id=supplier_id,
            historical_name=row["SHIIRESAKI_NM"].strip(),
            return_quantity=return_quantity,
            shipment_quantity=shipment_quantity,
            source_rate=source_rate,
        ),
        warnings,
    )


def parse_monthly_records(
    files: Iterable[MonthlyCsvData],
) -> tuple[tuple[MonthlyRecord, ...], tuple[WarningItem, ...]]:
    """CSV文字列を型変換し、継続可能な不正値を警告へ変換する。"""

    records: list[MonthlyRecord] = []
    warnings: list[WarningItem] = []
    for monthly_file in files:
        file_records: list[MonthlyRecord] = []
        file_warnings: list[WarningItem] = []
        if not monthly_file.rows:
            file_warnings.append(
                WarningItem(
                    code="EMPTY_MONTHLY_FILE",
                    message="Monthly CSV contains no data rows",
                    target_month=monthly_file.target_month,
                    source_file=monthly_file.source_path.name,
                )
            )
        for line_number, row in enumerate(monthly_file.rows, start=2):
            record, row_warnings = _parse_monthly_row(
                monthly_file,
                row,
                line_number,
            )
            file_warnings.extend(row_warnings)
            if record is not None:
                file_records.append(record)
        if not file_records:
            raise ValidationError(
                f"No valid data rows: {monthly_file.source_path.name}",
                tuple(file_warnings),
            )
        records.extend(file_records)
        warnings.extend(file_warnings)

    return tuple(records), tuple(warnings)
