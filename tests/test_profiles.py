from __future__ import annotations

import re
import subprocess
import sys
from typing import TYPE_CHECKING

import pytest
from fake_app import FORWARDER
from pydantic import ValidationError

from wily_client import ConflictError, Launch, ProfileOs, UnsupportedError, Wily

if TYPE_CHECKING:
    from pathlib import Path

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


def test_attach_to_a_running_profile(wily: Wily, fake: FakeApp, tmp_path: Path) -> None:
    """A profile started elsewhere (the app's window): CDP from its DevToolsActivePort, proxy from its process."""
    profile = wily.profiles.create(name='gui')
    with pytest.raises(ConflictError, match='does not run'):
        wily.profiles.attach(profile.id)

    launch = wily.profiles.launch(profile.id)
    user_data_dir = tmp_path / 'profiles' / profile.id
    assert launch.user_data_dir == user_data_dir
    # A stand-in for the browser's main process, with the switches the app gives it.
    browser = subprocess.Popen(  # noqa: S603
        [
            sys.executable,
            '-c',
            'import time; time.sleep(60)',
            f'--user-data-dir={user_data_dir}',
            '--proxy-server=http://127.0.0.1:47001',
            '--remote-debugging-port=0',
        ],
    )
    try:
        running = wily.profiles.attach(profile.id)
        assert running.pid == browser.pid
        assert running.proxy_server == 'http://127.0.0.1:47001'
        assert running.devtools.http_url == launch_devtools_url(wily, launch)
        wily.profiles.stop(running, timeout=5, interval=0.05)
    finally:
        browser.kill()
    assert fake.cdp_methods == ['Browser.close']
    with pytest.raises(ConflictError, match='does not run'):
        wily.profiles.attach(profile.id)  # the port is closed: a stale DevToolsActivePort is not a browser


def launch_devtools_url(wily: Wily, launch: Launch) -> str:
    return wily.profiles.devtools(launch, timeout=2).http_url


def test_proxy_of_a_profile_has_its_session_filled_and_the_forwarder_while_running(wily: Wily) -> None:
    """The two ways out through the profile's exit: the app's forwarder (while running) and the provider address."""
    proxy = wily.proxies.create(
        name='soax', protocol='http', host='proxy.soax.com', port=5000, username='pkg-1-sessionid-{session}', password='p@ss'
    )
    profile = wily.profiles.create(name='a', proxy_id=proxy.id)
    with pytest.raises(ValueError, match='profiles.proxy'):
        proxy.url()  # the template itself would be a session nobody else uses

    stopped = wily.profiles.proxy(profile.id)
    assert stopped is not None
    assert (stopped.running, stopped.proxy_server, stopped.name) == (False, None, 'soax')
    assert re.fullmatch(r'http://pkg-1-sessionid-[0-9a-f]{16}:p%40ss@proxy\.soax\.com:5000', stopped.upstream)
    assert 'p%40ss' not in repr(stopped)

    launch = wily.profiles.launch(profile.id)
    running = wily.profiles.proxy(profile.id)
    assert running is not None
    assert running.proxy_server == launch.proxy_server == FORWARDER
    assert running.upstream == stopped.upstream  # one session for the pair: the same exit as the browser

    assert wily.profiles.proxy(wily.profiles.create(name='b').id) is None


def test_proxy_of_a_profile_from_an_app_without_the_route(wily: Wily, fake: FakeApp) -> None:
    fake.routes = [r for r in fake.routes if not r[1].pattern.endswith('/proxy$')]
    with pytest.raises(UnsupportedError, match='update it'):
        wily.profiles.proxy(wily.profiles.create(name='a').id)
