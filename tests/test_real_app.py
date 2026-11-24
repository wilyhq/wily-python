"""Against a real `wily serve` (make test-real WILY_BIN=…): the library meets the app's own doors, on each OS.

Every test runs once per door, because each OS reaches the app differently and each way has broken on its own before:

- `default` — found through `desktop.json`: a Unix socket on macOS and Linux, a named pipe on Windows;
- `explicit` — a socket path or a pipe name the person set (`api_socket_path`), given to `Wily.connect(socket=…)`
  without reading the file: the documented way to name a pipe has to actually reach the app;
- `tcp` — the debug door (`api_tcp`), with its Bearer token.

CI runs it with the released CLI on macOS and Windows; Linux has no release yet. No sign-in is needed: health, the
sign-in state, the schema and the refusals answer without one.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

import pytest

from wily_client import AuthRequiredError, DoorKind, UnsupportedError, Wily

if TYPE_CHECKING:
    from collections.abc import Iterator

pytestmark = pytest.mark.real_app

THIS_OS_DOOR = DoorKind.NAMED_PIPE if sys.platform == 'win32' else DoorKind.UNIX_SOCKET
# What the app writes for a data directory of its own: `\\.\pipe\wily-<user>`, plus a suffix from the path when
# `WILY_DATA_DIR` moves it (wily-app `pipe::default_pipe_name`) so that two apps never share a pipe.
PIPE_NAME = re.compile(r'\\\\\.\\pipe\\wily-[A-Za-z0-9._-]+')


class Served(NamedTuple):
    door: str
    data_dir: Path
    discovery: dict[str, object]
    socket: str | None


def _binary() -> str:
    binary = os.environ.get('WILY_BIN', '')
    if not binary:
        pytest.skip('WILY_BIN is not set')
    return binary


def _chosen_socket(data_dir: Path) -> str:
    if sys.platform == 'win32':
        return rf'\\.\pipe\wily-python-test-{uuid.uuid4().hex[:8]}'
    return str(data_dir / 'w.sock')


def _setting(binary: str, env: dict[str, str], key: str, value: str) -> None:
    subprocess.run([binary, 'settings', 'set', key, value], env=env, check=True, capture_output=True, timeout=30)  # noqa: S603


@pytest.fixture(params=['default', 'explicit', 'tcp'])
def served(request: pytest.FixtureRequest) -> Iterator[Served]:
    binary = _binary()
    # A socket path may have at most 103 bytes on macOS, and pytest's tmp_path is deeper than that.
    data_dir = Path(tempfile.mkdtemp(prefix='wly'))
    env: dict[str, str] = {**os.environ, 'WILY_DATA_DIR': str(data_dir)}
    socket = None
    if request.param == 'explicit':
        socket = _chosen_socket(data_dir)
        _setting(binary, env, 'api_socket_path', socket)
    if request.param == 'tcp':
        _setting(binary, env, 'api_tcp', 'true')

    proc = subprocess.Popen([binary, 'serve'], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)  # noqa: S603
    discovery_file = data_dir / 'desktop.json'
    deadline = time.monotonic() + 30
    while not discovery_file.exists():
        if proc.poll() is not None or time.monotonic() > deadline:
            proc.kill()
            stderr = proc.stderr.read().decode(errors='replace') if proc.stderr else ''
            pytest.fail(f'wily serve wrote no desktop.json: {stderr[-2000:]}')
        time.sleep(0.2)
    discovery = json.loads(discovery_file.read_text(encoding='utf-8'))
    yield Served(request.param, data_dir, discovery, socket)
    proc.terminate()
    try:
        proc.wait(10)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture
def wily(served: Served) -> Iterator[Wily]:
    if served.door == 'explicit':
        client = Wily.connect(socket=served.socket)  # not through desktop.json: by the name alone
    elif served.door == 'tcp':
        client = Wily.connect(port=int(str(served.discovery['port'])), token=str(served.discovery['token']))
    else:
        client = Wily.connect(served.data_dir)
    with client:
        yield client


def test_health_and_sign_in_state(served: Served, wily: Wily) -> None:
    health = wily.app.health()
    assert health.app == 'wily'
    assert health.version
    assert not wily.app.auth_status().signed_in
    assert wily.door.kind is (DoorKind.TCP if served.door == 'tcp' else THIS_OS_DOOR)


def test_account_operations_need_a_sign_in(wily: Wily) -> None:
    with pytest.raises(AuthRequiredError):
        wily.proxies.list()
    with pytest.raises(AuthRequiredError):
        wily.profiles.list()


def test_profile_proxy_needs_a_sign_in_or_a_newer_app(wily: Wily) -> None:
    """0.1.6 has no `GET /v1/profiles/{id}/proxy`: a clear «update it», not a «no such profile»."""
    with pytest.raises((AuthRequiredError, UnsupportedError)):
        wily.profiles.proxy(str(uuid.uuid4()))


def test_schema_or_a_clear_answer(wily: Wily) -> None:
    try:
        schema = wily.app.openapi()
    except UnsupportedError:
        return  # 0.1.6 and older
    assert any(p.startswith('/v1/profiles') for p in schema['paths'])


def test_the_door_the_app_names_is_the_one_documented(served: Served) -> None:
    """`docs/connecting.md` tells people what to pass as `socket=`; this holds the app to it on each OS."""
    if served.door == 'tcp':
        assert served.discovery['token']
        return
    socket = str(served.discovery['socket'])
    if served.door == 'explicit':
        assert socket == served.socket
    elif sys.platform == 'win32':
        assert PIPE_NAME.fullmatch(socket), socket
    else:
        assert Path(socket).is_absolute()
        assert Path(socket).exists()


def test_a_wrong_token_is_refused(served: Served) -> None:
    if served.door != 'tcp':
        pytest.skip('only the TCP door has a token')
    with Wily.connect(port=int(str(served.discovery['port'])), token='wrong') as wily, pytest.raises(AuthRequiredError):
        wily.app.health()
