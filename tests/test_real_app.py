"""Against a real `wily serve` (make test-real WILY_BIN=…): the library meets the app's own door.

CI runs it with the released CLI on macOS and Windows; Linux has no release yet. No sign-in is needed:
health, the sign-in state and the schema answer without one.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from wily_client import AuthRequiredError, UnsupportedError, Wily

if TYPE_CHECKING:
    from collections.abc import Iterator

pytestmark = pytest.mark.real_app


@pytest.fixture
def served() -> Iterator[Path]:
    binary = os.environ.get('WILY_BIN', '')
    if not binary:
        pytest.skip('WILY_BIN is not set')
    # A socket path may have at most 103 bytes on macOS, and pytest's tmp_path is deeper than that.
    tmp_path = Path(tempfile.mkdtemp(prefix='wly'))
    env: dict[str, str] = {**os.environ, 'WILY_DATA_DIR': str(tmp_path)}
    proc = subprocess.Popen([binary, 'serve'], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)  # noqa: S603
    deadline = time.monotonic() + 30
    while not (tmp_path / 'desktop.json').exists():
        if proc.poll() is not None or time.monotonic() > deadline:
            proc.kill()
            stderr = proc.stderr.read().decode(errors='replace') if proc.stderr else ''
            pytest.fail(f'wily serve wrote no desktop.json: {stderr[-2000:]}')
        time.sleep(0.2)
    yield tmp_path
    proc.terminate()
    try:
        proc.wait(10)
    except subprocess.TimeoutExpired:
        proc.kill()


def test_health_over_the_default_door(served: Path) -> None:
    with Wily.connect(served) as wily:
        health = wily.app.health()
        assert health.app == 'wily'
        assert health.version
        assert not wily.app.auth_status().signed_in


def test_schema_or_a_clear_answer(served: Path) -> None:
    with Wily.connect(served) as wily:
        try:
            schema = wily.app.openapi()
        except UnsupportedError:
            return  # 0.1.6 and older
        assert any(p.startswith('/v1/profiles') for p in schema['paths'])


def test_account_operations_need_a_sign_in(served: Path) -> None:
    with Wily.connect(served) as wily, pytest.raises(AuthRequiredError):
        wily.proxies.list()
