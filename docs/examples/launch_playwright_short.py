"""The same as launch_playwright.py in one block: `running()` launches, yields the CDP endpoint, stops."""

import sys

from playwright.sync_api import sync_playwright

from wily_client import Wily


def main(name: str) -> None:
    with Wily.connect() as wily, wily.profiles.running(wily.profiles.find(name).id) as devtools, sync_playwright() as pw:
        page = pw.chromium.connect_over_cdp(devtools.http_url).contexts[0].new_page()
        page.goto('https://wily.bot/')
        print(page.title())
    # here the browser is closed and the profile is stopped


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'shop-de-1')
