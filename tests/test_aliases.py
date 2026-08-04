"""仕入先名エイリアスのテスト。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from supplier_quality_trend.aliases import (
    AliasError,
    normalize_supplier_name,
    read_alias_rules,
)


class AliasTest(unittest.TestCase):
    def _write(self, content: str) -> Path:
        directory = Path(self._temporary.name)
        path = directory / "aliases.csv"
        path.write_text(content, encoding="utf-8")
        return path

    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self._temporary.cleanup()

    def test_enabled_is_case_insensitive_and_false_is_skipped(self) -> None:
        path = self._write(
            "CANONICAL_GROUP_NM,ALIAS_SUPPLIER_NM,ENABLED,NOTE\n"
            "グループA, 仕入先A ,true,有効\n"
            "グループB,仕入先B,FALSE,無効\n"
        )
        rules = read_alias_rules(path)
        self.assertEqual(rules["仕入先A"].canonical_group_name, "グループA")
        self.assertNotIn("仕入先B", rules)

    def test_conflicting_alias_stops_processing(self) -> None:
        path = self._write(
            "CANONICAL_GROUP_NM,ALIAS_SUPPLIER_NM,ENABLED,NOTE\n"
            "グループA,仕入先A,TRUE,\n"
            "グループB,仕入先A,TRUE,\n"
        )
        with self.assertRaises(AliasError):
            read_alias_rules(path)

    def test_normalization_trims_only_edges(self) -> None:
        self.assertEqual(normalize_supplier_name(" 仕入先Ａ "), "仕入先Ａ")
        self.assertNotEqual(
            normalize_supplier_name("仕入先Ａ"),
            normalize_supplier_name("仕入先A"),
        )


if __name__ == "__main__":
    unittest.main()
