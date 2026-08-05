"""ブラウザ合算ロジックの確認。"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CombineJsTest(unittest.TestCase):
    def test_combine_js_quantity_totals(self) -> None:
        script = ROOT / "tests" / "js" / "run_combine_tests.js"
        completed = subprocess.run(
            ["node", str(script)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            completed.stdout + completed.stderr,
        )


if __name__ == "__main__":
    unittest.main()
