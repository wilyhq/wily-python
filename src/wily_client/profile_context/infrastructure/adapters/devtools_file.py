"""Chromium started with `--remote-debugging-port=0` writes the port it took into `DevToolsActivePort`."""

from __future__ import annotations

from typing import TYPE_CHECKING

from wily_client.profile_context.domains.value_objects.profile import DevTools

if TYPE_CHECKING:
    from pathlib import Path

FILE = 'DevToolsActivePort'
LINES = 2  # the port, then the browser target's path


class DevToolsFileAdapter:
    def read(self, user_data_dir: Path) -> DevTools | None:
        try:
            lines = (user_data_dir / FILE).read_text(encoding='utf-8').splitlines()
        except OSError:
            return None
        if len(lines) < LINES or not lines[0].strip().isdigit():
            return None  # written but not flushed yet: try again
        return DevTools(port=int(lines[0]), browser_path=lines[1].strip())
