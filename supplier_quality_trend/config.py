"""Git管理外のローカル設定を読み込む。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


class SettingsError(ValueError):
    """設定ファイルの仕様違反。"""


@dataclass(frozen=True)
class Settings:
    """MVPで必要な入力パス。"""

    monthly_csv_directory: Path
    supplier_master_file: Path


def _resolve_user_home_path(value: object, key: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise SettingsError(f"Invalid setting: {key}")
    if "<" in value or ">" in value:
        raise SettingsError(f"Placeholder is not allowed in local setting: {key}")
    configured = Path(value)
    if configured.is_absolute():
        return configured
    return Path.home() / configured


def load_settings(path: Path) -> Settings:
    """JSON設定を読み込み、相対パスをユーザーホーム基準で解決する。"""

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SettingsError(f"Cannot read settings: {path}") from exc

    if not isinstance(raw, dict):
        raise SettingsError("Settings root must be an object")

    return Settings(
        monthly_csv_directory=_resolve_user_home_path(
            raw.get("monthly_csv_directory"),
            "monthly_csv_directory",
        ),
        supplier_master_file=_resolve_user_home_path(
            raw.get("supplier_master_file"),
            "supplier_master_file",
        ),
    )
