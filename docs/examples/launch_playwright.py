"""Launch one profile, drive its browser with Playwright over CDP, stop the profile.

    pip install playwright        # no `playwright install`: the browser is wily's
    python docs/examples/launch_playwright.py "shop-de-1"

The three steps, each on its own:
1. `launch` — the app starts the profile's browser on this machine, through the profile's proxy, with its
   cookies; a browser window opens.
2. `devtools` — the CDP endpoint that browser opened; Playwright connects to it with `connect_over_cdp`.
3. `stop` — closes the browser (CDP `Browser.close`) and waits until the app has saved the profile and
   released it. Playwright's own `browser.close()` only disconnects from a browser it did not start.
"""

import sys

from playwright.sync_api import sync_playwright

from wily_client import Wily


def main(name: str) -> None:
    with Wily.connect() as wily:
        profile = wily.profiles.find(name)

        # 1. Start the profile: a browser window opens.
        launch = wily.profiles.launch(profile.id)
        for warning in launch.warnings:
            print('warning:', warning)  # e.g. the profile's core is missing and another one was used

        try:
            # 2. Connect Playwright to that browser over CDP.
            devtools = wily.profiles.devtools(launch)  # waits until the browser has opened its port
            print('CDP at', devtools.http_url)
            with sync_playwright() as pw:
                browser = pw.chromium.connect_over_cdp(devtools.http_url)
                context = browser.contexts[0]  # the profile's own context: its cookies, its proxy
                page = context.new_page()
                page.goto('https://wily.bot/')
                print(page.title())
                # ... the work ...
        finally:
            # 3. Stop the profile, even if the work above failed.
            stopped = wily.profiles.stop(launch)
            print(stopped.name, 'is', stopped.state)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'shop-de-1')
