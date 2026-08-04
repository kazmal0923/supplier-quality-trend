"""月次不良率CSVの検出と読込。"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

REQUIRED_COLUMNS: Final[tuple[str, ...]] = (
    "SHIIRESAKI_ID",
    "SHIIRESAKI_NM",
    "HENPIN_SU",
    "SYUKKA_SU",
    "DEFECTIVE_RATE",
)
_MONTHLY_FILENAME = re.compile(
    r"^(?P<year>\d{4})年(?P<month>0[1-9]|1[0-2])月\.csv$"
)


class MonthlyCsvError(ValueError):
    """月次CSVの仕様違反。"""


@dataclass(frozen=True)
class MonthlyCsvData:
    """1か月分の月次CSV読込結果。"""

    source_path: Path
    target_month: str
    rows: tuple[dict[str, str], ...]


def parse_target_month(filename: str) -> str:
    """YYYY年MM月.csvからYYYY-MMを返す。"""

    match = _MONTHLY_FILENAME.fullmatch(filename)
    if match is None:
        raise MonthlyCsvError(f"Invalid monthly CSV filename: {filename}")
    return f"{match.group('year')}-{match.group('month')}"


def read_monthly_csv(path: Path) -> MonthlyCsvData:
    """UTF-8（BOM可）の月次CSVを読み込む。"""

    target_month = parse_target_month(path.name)
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source, delimiter=",")
            fieldnames = tuple(reader.fieldnames or ())
            missing = [
                column for column in REQUIRED_COLUMNS if column not in fieldnames
            ]
            if missing:
                raise MonthlyCsvError(
                    f"Missing required columns in {path.name}: {', '.join(missing)}"
                )
            rows = tuple(
                {
                    column: row.get(column) or ""
                    for column in REQUIRED_COLUMNS
                }
                for row in reader
            )
    except UnicodeDecodeError as exc:
        raise MonthlyCsvError(f"Monthly CSV is not UTF-8: {path.name}") from exc
    except OSError as exc:
        raise MonthlyCsvError(f"Cannot read monthly CSV: {path}") from exc

    return MonthlyCsvData(
        source_path=path,
        target_month=target_month,
        rows=rows,
    )


def discover_monthly_csvs(directory: Path) -> tuple[MonthlyCsvData, ...]:
    """フォルダ内のCSVを年月順に読み込む。"""

    if not directory.is_dir():
        raise MonthlyCsvError(f"Monthly CSV directory not found: {directory}")

    paths = sorted(directory.glob("*.csv"), key=lambda path: path.name)
    if not paths:
        raise MonthlyCsvError(f"No monthly CSV files found: {directory}")

    loaded = tuple(read_monthly_csv(path) for path in paths)
    months = [item.target_month for item in loaded]
    if len(months) != len(set(months)):
        raise MonthlyCsvError("Duplicate monthly CSV target month")
    return tuple(sorted(loaded, key=lambda item: item.target_month))
