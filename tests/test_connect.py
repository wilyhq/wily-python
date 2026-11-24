from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from wily_client import DoorKind, UnavailableError, UnsupportedError, Wily
from wily_client.common.infrastructure.data_dir import data_dir

if TYPE_CHECKING:
    from fake_app import FakeApp


def test_health_and_auth_over_this_os_door(wily: Wily) -> None:
    assert wily.app.health().version == '0.1.7'
    assert wily.app.auth_status().signed_in
    assert wily.app.whoami().email == 'someone@example.com'
    assert wily.app.openapi()['openapi'] == '3.1.0'


def test_door_matches_the_os(wily: Wily) -> None:
    expected = {DoorKind.TCP, DoorKind.NAMED_PIPE if sys.platform == 'win32' else DoorKind.UNIX_SOCKET}
    assert wily.door.kind in expected


def test_no_discovery_file_means_not_running(tmp_path: Path) -> None:
    with pytest.raises(UnavailableError, match='not running'):
        Wily.connect(tmp_path)


def test_dead_door_is_unavailable(tmp_path: Path) -> None:
    (tmp_path / 'desktop.json').write_text(json.dumps({'pid': 1, 'port': 9, 'token': 't', 'app': 'x'}))
    with Wily.connect(tmp_path) as w, pytest.raises(UnavailableError, match='cannot reach'):
        w.app.health()


def test_wrong_token_is_refused(data_dir: Path) -> None:
    d = json.loads((data_dir / 'desktop.json').read_text())
    if 'port' not in d:
        pytest.skip('only the TCP door takes a token')
    with Wily.connect(port=d['port'], token='wrong') as w, pytest.raises(Exception, match='token'):  # noqa: PT011
        w.app.health()


def test_openapi_missing_on_old_app(wily: Wily, fake: FakeApp) -> None:
    fake.routes = [r for r in fake.routes if r[1].pattern != '^/openapi.json$']
    with pytest.raises(UnsupportedError, match='0.1.6'):
        wily.app.openapi()


@pytest.mark.parametrize(
    ('platform', 'env', 'expected'),
    [
        ('darwin', {}, 'H/Library/Application Support/bot.wily.wily'),
        ('win32', {'APPDATA': 'C:/Users/me/AppData/Roaming'}, 'C:/Users/me/AppData/Roaming/wily/wily/data'),
        ('linux', {}, 'H/.local/share/wily'),
        ('linux', {'XDG_DATA_HOME': '/xdg'}, '/xdg/wily'),
        ('linux', {'WILY_DATA_DIR': '/moved'}, '/moved'),
    ],
)
def test_data_dir_per_os(platform: str, env: dict[str, str], expected: str) -> None:
    assert data_dir(platform, env, Path('H')) == Path(expected)
