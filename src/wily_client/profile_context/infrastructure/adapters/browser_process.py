"""Finds a profile's browser process by its `--user-data-dir`, and reads its switches — on all three OSes."""

from __future__ import annotations

from typing import TYPE_CHECKING

import psutil

if TYPE_CHECKING:
    from pathlib import Path

USER_DATA_DIR = '--user-data-dir='


class BrowserProcessAdapter:
    def find_browser(self, user_data_dir: Path) -> tuple[int, list[str]] | None:
        """The browser's main process (not a renderer or GPU helper, which carry `--type=`).

        Several processes can carry the same switches — a launcher that re-runs itself as its child, as a venv's
        `python.exe` does on Windows — so the topmost of them is the one: its parent is not among the matches."""
        wanted = str(user_data_dir)
        found: dict[int, tuple[int | None, list[str]]] = {}
        for proc in psutil.process_iter(['pid', 'ppid', 'cmdline']):
            args = proc.info.get('cmdline') or []
            if any(a.startswith('--type=') for a in args):
                continue
            if any(a.startswith(USER_DATA_DIR) and _same(a[len(USER_DATA_DIR) :], wanted) for a in args):
                found[proc.info['pid']] = (proc.info.get('ppid'), args)
        for pid, (ppid, args) in found.items():
            if ppid not in found:
                return pid, args
        return None


def _same(found: str, wanted: str) -> bool:
    return found.strip('"').rstrip('/\\').casefold() == wanted.rstrip('/\\').casefold()
