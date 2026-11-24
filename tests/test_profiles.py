from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from wily_client import ConflictError, ProfileOs, Wily

if TYPE_CHECKING:
    from fake_app import FakeApp


def test_profile_lifecycle(wily: Wily) -> None:
    proxy = wily.proxies.create(name='p', protocol='http', host='h.example', port=3128)
    profile = wily.profiles.create(
        name='shop-1',
        os=ProfileOs.WINDOWS11,
        proxy_id=proxy.id,
        tags=['shop'],
        start_url='https://wily.bot/',
        launch_args=['--start-maximized'],
    )
    assert profile.proxy is not None
    assert profile.proxy.name == 'p'
    assert not profile.running

    assert wily.profiles.find('shop-1') == profile
    copy = wily.profiles.clone(profile.id)
    assert copy.name == 'shop-1 (copy)'

    wily.profiles.delete(copy.id)
    assert copy.id not in {p.id for p in wily.profiles.list()}
    assert copy.id in {p.id for p in wily.profiles.list(trash=True)}
    assert not wily.profiles.restore(copy.id).trashed


def test_update_refuses_a_lost_change(wily: Wily) -> None:
    profile = wily.profiles.create(name='a')
    seen = wily.profiles.get(profile.id)
    assert seen.etag == '"1"'
    wily.profiles.update(profile.id, notes='changed elsewhere')
    with pytest.raises(ConflictError):
        wily.profiles.update(seen, notes='mine')
    assert wily.profiles.update(wily.profiles.get(profile.id), notes='mine').notes == 'mine'


def test_launch_devtools_and_stop(wily: Wily, fake: FakeApp) -> None:
    profile = wily.profiles.create(name='run')
    launch = wily.profiles.launch(profile.id)
    assert launch.pid == 777
    assert launch.session_id == 's1'
    devtools = wily.profiles.devtools(launch, timeout=2)
    assert devtools.http_url == f'http://127.0.0.1:{devtools.port}'
    assert devtools.ws_url.endswith('/devtools/browser/abc')
    with pytest.raises(ConflictError, match='already running'):
        wily.profiles.launch(profile.id)
    stopped = wily.profiles.stop(launch, timeout=5, interval=0.05)
    assert not stopped.running
    assert fake.cdp_methods == ['Browser.close']


def test_running_stops_even_when_the_block_fails(wily: Wily, fake: FakeApp) -> None:
    profile = wily.profiles.create(name='ctx')
    with pytest.raises(RuntimeError), wily.profiles.running(profile.id) as devtools:
        assert devtools.port
        raise RuntimeError
    assert not wily.profiles.get(profile.id).running
    assert fake.cdp_methods == ['Browser.close']


@pytest.mark.parametrize(
    'bad',
    [
        {'launch_args': ['--remote-debugging-port=9222']},
        {'launch_args': ['--proxy-server=x']},
        {'launch_args': ['start-maximized']},
        {'launch_args': ['--x'] * 51},
        {'start_url': 'file:///etc/passwd'},
        {'os': 'amiga'},
        {'webrtc': 'sometimes'},
        {'proxy_id': 'not-a-uuid'},
        {'timezone': 'Europe Berlin'},
    ],
)
def test_draft_is_validated_before_sending(wily: Wily, bad: dict) -> None:
    with pytest.raises(ValidationError):
        wily.profiles.create(name='x', **bad)


def test_folders(wily: Wily) -> None:
    folder = wily.profiles.create_folder('Shops')
    assert [f.name for f in wily.profiles.folders()] == ['Shops']
    assert folder.id
