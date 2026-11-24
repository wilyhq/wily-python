from __future__ import annotations

import json
import os
import sys
import tempfile
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from fake_app import FakeApp, serve_pipe, serve_tcp, serve_unix

from wily_client import Wily

if TYPE_CHECKING:
    from collections.abc import Iterator

# This OS's own door, and the debug TCP door everywhere.
DOORS = ['pipe' if sys.platform == 'win32' else 'unix', 'tcp']


@pytest.fixture
def fake(tmp_path: Path) -> FakeApp:
    return FakeApp(tmp_path / 'profiles')  # where the app keeps profiles: <data dir>/profiles/<id>


@pytest.fixture(params=DOORS)
def data_dir(request: pytest.FixtureRequest, fake: FakeApp, tmp_path: Path) -> Iterator[Path]:
    """A data directory whose `desktop.json` points at the fake app behind one door."""
    if request.param == 'tcp':
        door = serve_tcp(fake, token=uuid.uuid4().hex)
    elif request.param == 'pipe':
        door = serve_pipe(fake, rf'\\.\pipe\wily-client-test-{uuid.uuid4().hex[:12]}')
    else:
        # AF_UNIX paths are limited to ~104 bytes on macOS: pytest's tmp_path is too deep.
        sock = Path(tempfile.mkdtemp(prefix='wly')) / 'w.sock'
        door = serve_unix(fake, str(sock))
    discovery = {'version': 2, 'pid': os.getpid(), 'app': 'wily serve', 'app_version': '0.1.7', **door.discovery}
    (tmp_path / 'desktop.json').write_text(json.dumps(discovery), encoding='utf-8')
    yield tmp_path
    door.stop()


@pytest.fixture
def wily(data_dir: Path) -> Iterator[Wily]:
    with Wily.connect(data_dir) as w:
        yield w
