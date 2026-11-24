"""A profile already running on this machine — started from the app's window or by another script:
take its CDP endpoint and its proxy, drive it with Playwright, and stop it if you want.

    python docs/examples/attach_running.py "shop-de-1" [--stop]
"""

import sys

import httpx
from playwright.sync_api import sync_playwright

from wily_client import Wily


def main(name: str) -> None:
    with Wily.connect() as wily:
        profile = wily.profiles.find(name)
        running = wily.profiles.attach(profile.id)  # ConflictError if its browser does not run here

        print('pid          ', running.pid)
        print('CDP          ', running.devtools.http_url, running.devtools.ws_url)
        # What the browser connects through: the proxy itself, or the app's local forwarder
        # (http://127.0.0.1:<port>) for a proxy with a login — usable from this machine without the password.
        print('proxy_server ', running.proxy_server)

        # The profile's proxy as the app connects to it. Two ways to leave through the browser's exit:
        #   proxy_server — the app's local forwarder the browser uses (no password needed, only while it runs);
        #   upstream     — the provider's address with this profile's login, {session} filled by the server
        #                  (carries the password: never print or log it whole).
        proxy = wily.profiles.proxy(profile.id)
        if proxy:
            forwarder = proxy.proxy_server or running.proxy_server  # None from the app when another one started it
            print('proxy        ', proxy.name, '| forwarder', forwarder)
            via_forwarder = httpx.get('https://api.ipify.org', proxy=forwarder, timeout=30).text
            via_upstream = httpx.get('https://api.ipify.org', proxy=proxy.upstream, timeout=30).text
            print('exit IP      ', via_forwarder, '(forwarder)', via_upstream, '(upstream)')

        with sync_playwright() as pw:
            page = pw.chromium.connect_over_cdp(running.devtools.http_url).contexts[0].new_page()
            page.goto('https://wily.bot/')
            print('title        ', page.title())

        if '--stop' in sys.argv:  # by default it stays running for whoever started it
            print('stopped      ', wily.profiles.stop(running).state)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'shop-de-1')
