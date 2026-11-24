from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from pydantic import ValidationError

from wily_client import NotFoundError, ProxyDraft, ProxyProtocol, Wily

if TYPE_CHECKING:
    from fake_app import FakeApp


def test_proxy_crud_and_check(wily: Wily) -> None:
    proxy = wily.proxies.create(
        name='de-1',
        protocol='socks5',
        host='gate.example.net',
        port=1080,
        username='user-{session}',
        password='p@ss',
        country='de',
    )
    assert proxy.protocol is ProxyProtocol.SOCKS5
    assert proxy.country == 'DE'
    assert proxy.alive is None
    assert 'p@ss' not in repr(proxy)
    assert proxy.url() == 'socks5://user-%7Bsession%7D:p%40ss@gate.example.net:1080'

    assert [p.name for p in wily.proxies.list()] == ['de-1']
    assert wily.proxies.find('de-1') == proxy

    renamed = wily.proxies.update(proxy.id, name='de-2')
    assert renamed.name == 'de-2'

    check = wily.proxies.check(proxy.id)
    assert check.ok
    assert check.exit_country == 'DE'
    assert wily.proxies.get(proxy.id).alive is True

    wily.proxies.delete(proxy.id)
    with pytest.raises(NotFoundError) as e:
        wily.proxies.get(proxy.id)
    assert e.value.exit_code == 5


def test_only_set_fields_are_sent(wily: Wily, fake: FakeApp) -> None:
    p = wily.proxies.create(ProxyDraft(name='x', protocol=ProxyProtocol.HTTP, host='h', port=8080))
    wily.proxies.update(p.id, notes='n')
    _, _, _, body = fake.requests[-1]
    assert body == {'notes': 'n'}


@pytest.mark.parametrize(
    'bad',
    [
        {'port': 0},
        {'port': 70000},
        {'protocol': 'ftp'},
        {'host': 'a b'},
        {'country': 'Germany'},
        {'name': '  '},
        {'unknown_field': 1},
    ],
)
def test_draft_is_validated_before_sending(wily: Wily, fake: FakeApp, bad: dict[str, Any]) -> None:
    fields: dict[str, Any] = {'name': 'x', 'protocol': 'http', 'host': 'h.example', 'port': 8080, **bad}
    before = len(fake.requests)
    with pytest.raises(ValidationError):
        wily.proxies.create(**fields)
    assert len(fake.requests) == before


def test_import_is_dry_by_default(wily: Wily) -> None:
    assert wily.proxies.import_text('h1:1\nh2:2\n') == {'parsed': 2, 'created': 0}
    assert wily.proxies.import_text('h1:1', dry_run=False)['created'] == 1
