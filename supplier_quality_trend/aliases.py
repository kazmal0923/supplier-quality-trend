"""仕入先名エイリアス設定の読込。"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Final

from supplier_quality_trend.models import AliasRule

ALIAS_COLUMNS: Final[tuple[str, ...]] = (
    "CANONICAL_GROUP_NM",
    "ALIAS_SUPPLIER_NM",
    "ENABLED",
    "NOTE",
)


class AliasError(ValueError):
    """エイリアス設定の仕様違反。"""


def normalize_supplier_name(value: str) -> str:
    """仕様どおり前後空白だけを除去する。"""

    return value.strip()


def read_alias_rules(path: Path) -> dict[str, AliasRule]:
    """UTF-8のエイリアスCSVから有効な定義を読み込む。"""

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source, delimiter=",")
            fieldnames = tuple(reader.fieldnames or ())
            missing = [column for column in ALIAS_COLUMNS if column not in fieldnames]
            if missing:
                raise AliasError(
                    f"Missing alias columns: {', '.join(missing)}"
                )

            rules: dict[str, AliasRule] = {}
            for row in reader:
                enabled = (row.get("ENABLED") or "").strip().upper()
                if enabled not in {"TRUE", "FALSE"}:
                    raise AliasError("ENABLED must be TRUE or FALSE")
                if enabled == "FALSE":
                    continue

                alias_name = normalize_supplier_name(
                    row.get("ALIAS_SUPPLIER_NM") or ""
                )
                canonical_name = normalize_supplier_name(
                    row.get("CANONICAL_GROUP_NM") or ""
                )
                if not alias_name or not canonical_name:
                    raise AliasError("Enabled alias names must not be empty")

                existing = rules.get(alias_name)
                if (
                    existing is not None
                    and existing.canonical_group_name != canonical_name
                ):
                    raise AliasError(
                        f"Alias is assigned to multiple groups: {alias_name}"
                    )
                rules[alias_name] = AliasRule(
                    canonical_group_name=canonical_name,
                    alias_supplier_name=alias_name,
                    note=(row.get("NOTE") or "").strip(),
                )
    except UnicodeDecodeError as exc:
        raise AliasError("Alias CSV is not UTF-8") from exc
    except OSError as exc:
        raise AliasError(f"Cannot read alias CSV: {path}") from exc

    return rules
