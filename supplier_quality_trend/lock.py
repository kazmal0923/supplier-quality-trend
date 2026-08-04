"""バッチの二重起動を防止するロック。"""

from __future__ import annotations

import msvcrt
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, Iterator


class AlreadyRunningError(RuntimeError):
    """別のバッチ処理が実行中。"""


def _try_lock(lock_file: BinaryIO) -> None:
    lock_file.seek(0)
    try:
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError as exc:
        raise AlreadyRunningError("Batch is already running") from exc


@contextmanager
def exclusive_run_lock(root: Path) -> Iterator[None]:
    """Windowsのファイルロックを保持し、二重起動を防止する。"""

    lock_path = root / "logs" / "supplier-quality-trend.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock_file:
        if lock_file.seek(0, 2) == 0:
            lock_file.write(b"0")
            lock_file.flush()
        _try_lock(lock_file)
        try:
            lock_file.seek(0)
            lock_file.write(b"1")
            lock_file.flush()
            yield
        finally:
            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
