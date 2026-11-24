"""Where the app keeps its data, and with it `desktop.json` — the same rule as the app uses.

`WILY_DATA_DIR` moves everything; otherwise the OS data directory of `ProjectDirs("bot", "wily", "wily")`:

| OS | data directory |
|---|---|
| macOS | `~/Library/Application Support/bot.wily.wily` |
| Windows | `%APPDATA%\\wily\\wily\\data` |
| Linux | `$XDG_DATA_HOME/wily`, else `~/.local/share/wily` |
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

DISCOVERY_FILE = 'desktop.json'


def data_dir(platform: str = sys.platform, env: dict[str, str] | None = None, home: Path | None = None) -> Path:
    env = dict(os.environ) if env is None else env
    home = Path.home() if home is None else home
    if moved := env.get('WILY_DATA_DIR'):
        return Path(moved)
    if platform == 'darwin':
        return home / 'Library' / 'Application Support' / 'bot.wily.wily'
    if platform == 'win32':
        roaming = env.get('APPDATA') or str(home / 'AppData' / 'Roaming')
        return Path(roaming) / 'wily' / 'wily' / 'data'
    xdg = env.get('XDG_DATA_HOME')
    base = Path(xdg) if xdg and Path(xdg).is_absolute() else home / '.local' / 'share'
    return base / 'wily'


def discovery_path(directory: Path | None = None) -> Path:
    return (directory or data_dir()) / DISCOVERY_FILE
