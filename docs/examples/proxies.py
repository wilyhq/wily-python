"""Proxies: create, check, change, list, delete."""

from wily_client import ProxyDraft, ProxyKind, ProxyProtocol, Wily


def main() -> None:
    with Wily.connect() as wily:
        # Values are checked by pydantic before anything is sent: a port of 0 or a country of
        # 'Germany' raises pydantic.ValidationError here, not an answer from the app.
        draft = ProxyDraft(
            name='de-residential-1',
            protocol=ProxyProtocol.SOCKS5,
            host='gate.example.net',
            port=1080,
            username='customer-{session}',
            password='secret',
            kind=ProxyKind.RESIDENTIAL,
            country='de',
        )
        check = wily.proxies.check_draft(draft)  # before saving
        print('exit', check.exit_ip, check.exit_country, check.latency_ms, 'ms')

        proxy = wily.proxies.create(draft)
        proxy = wily.proxies.update(proxy.id, notes='bought 2026-11')  # only `notes` is sent
        print(proxy.name, proxy.url(with_credentials=False))

        for p in wily.proxies.list():
            print(f'{p.name:24} {p.protocol.value:7} {p.country or "--"} alive={p.alive}')

        wily.proxies.delete(proxy.id)

        # A pasted list, one per line; the default only parses and reports.
        print(wily.proxies.import_text('socks5://u:p@1.2.3.4:1080\nhttp://5.6.7.8:3128'))


if __name__ == '__main__':
    main()
