"""Finds a profile's browser process by its `--user-data-dir`, and reads its switches — on all three OSes."""

from __future__ import annotations

from typing import TYPE_CHECKING

import psutil

if TYPE_CHECKING:
    from pathlib import Path

USER_DATA_DIR = '--user-data-dir='


class BrowserProcessAdapter:
    def find_browser(self, user_data_dir: Path) -> tuple[int, list[str]] | None:
        """The browser's main process (not a renderer or GPU helper, which carry `--type=`)."""
        wanted = str(user_data_dir)
        for proc in psutil.process_iter(['pid', 'cmdline']):
            args = proc.info.get('cmdline') or []
            if any(a.startswith('--type=') for a in args):
                continue
            if any(a.startswith(USER_DATA_DIR) and _same(a[len(USER_DATA_DIR) :], wanted) for a in args):
                return proc.info['pid'], args
        return None


def _same(found: str, wanted: str) -> bool:
    return found.strip('"').rstrip('/\\').casefold() == wanted.rstrip('/\\').casefold()
