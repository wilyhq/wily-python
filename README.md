# wily-client

Drive the [wily](https://wily.bot/) desktop app from Python: create and check proxies, create and change browser
profiles, launch them and hand the browser to Playwright.

Works on **macOS, Windows and Linux**. The library talks to the app's local API over its own door — a Unix socket on
macOS and Linux, a named pipe on Windows — so no port is opened and no token is needed.

```sh
pip install "wily-client @ git+https://github.com/wilyhq/wily-python"
```

```python
from wily_client import Wily

with Wily.connect() as wily:                       # finds the running app through desktop.json
    proxy = wily.proxies.create(name='de-1', protocol='socks5', host='gate.example.net', port=1080,
                                username='user', password='secret', country='de')
    print(wily.proxies.check(proxy.id).exit_ip)

    profile = wily.profiles.create(name='shop-1', proxy_id=proxy.id, os='windows11')
    with wily.profiles.running(profile.id) as devtools:  # browser opens through the proxy, stops at the end
        print(devtools.http_url)                         # CDP endpoint for Playwright / Puppeteer
```

Requires Python 3.11+ and a running wily app (or `wily serve` on a machine without a window); profiles and proxies
need a signed-in account.

## Documentation

| | |
|---|---|
| [docs/install.md](docs/install.md) | install the library and the app, on each OS |
| [docs/connecting.md](docs/connecting.md) | how the library finds the app: `desktop.json`, socket, pipe, TCP |
| [docs/proxies.md](docs/proxies.md) | proxies: create, check, change, import, delete |
| [docs/profiles.md](docs/profiles.md) | profiles and folders, safe updates, launching, Playwright |
| [docs/errors.md](docs/errors.md) | the error classes and what to do with each |
| [docs/examples/](docs/examples/) | runnable scripts for all of the above |
| [docs/development.md](docs/development.md) | working on the library: `make` targets, tests, CI, releasing |
| [docs/architecture/OVERVIEW.md](docs/architecture/OVERVIEW.md) | how the code is laid out (DDD, hexagonal) |

The same guides are on the site: https://wily.bot/docs/libraries/.

## License

MIT
