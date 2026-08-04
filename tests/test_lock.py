"""二重起動防止ロックのテスト。"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from supplier_quality_trend.lock import (
    AlreadyRunningError,
    exclusive_run_lock,
)


class LockTest(unittest.TestCase):
    def test_second_lock_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            lock_path = root / "logs/supplier-quality-trend.lock"
            with exclusive_run_lock(root):
                self.assertTrue(lock_path.exists())
                with self.assertRaises(AlreadyRunningError):
                    with exclusive_run_lock(root):
                        pass
            self.assertTrue(lock_path.exists())

    def test_lock_is_released_after_context(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with exclusive_run_lock(root):
                pass
            with exclusive_run_lock(root):
                pass

    def test_lock_is_released_after_exception(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(RuntimeError, "simulated"):
                with exclusive_run_lock(root):
                    raise RuntimeError("simulated")
            with exclusive_run_lock(root):
                pass

    def test_other_process_blocks_and_termination_releases_lock(self) -> None:
        code = (
            "import sys,time\n"
            "from pathlib import Path\n"
            "from supplier_quality_trend.lock import exclusive_run_lock\n"
            "with exclusive_run_lock(Path(sys.argv[1])):\n"
            " print('READY', flush=True)\n"
            " time.sleep(60)\n"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with subprocess.Popen(
                [sys.executable, "-c", code, str(root)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            ) as process:
                try:
                    self.assertEqual(process.stdout.readline().strip(), "READY")
                    with self.assertRaises(AlreadyRunningError):
                        with exclusive_run_lock(root):
                            pass
                finally:
                    process.terminate()
                    process.wait(timeout=5)
            with exclusive_run_lock(root):
                pass


if __name__ == "__main__":
    unittest.main()
