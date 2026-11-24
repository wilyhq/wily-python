"""Launch a profile and drive its browser with Playwright over CDP.

`pip install playwright` — no `playwright install` is needed: the browser is wily's.
"""

import sys

from playwright.sync_api import sync_playwright

from wily_client import Wily


def main(name: str) -> None:
    with Wily.connect() as wily:
        profile = wily.profiles.find(name)
        launch = wily.profiles.launch(profile.id)  # the app starts the browser through the profile's proxy
        for warning in launch.warnings:
            print('warning:', warning)
        devtools = wily.profiles.devtools(launch)  # waits until the browser writes its CDP port

    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(devtools.http_url)
        page = browser.contexts[0].new_page()
        page.goto('https://wily.bot/')
        print(page.title())
        browser.close()  # disconnects; closing the window ends the profile's session


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'shop-de-1')
