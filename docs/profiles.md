# Profiles — `wily.profiles`

A profile is one browser identity: its OS, proxy, time zone, language, WebRTC mode, cookies. Profiles belong to the
account; launching one starts a real browser on **this** machine.

| call | does |
|---|---|
| `list(q=…, folder_id=…, tag=…, proxy_id=…, trash=…)` | profiles, filtered → `list[Profile]` |
| `get(id)` / `find(name)` | one profile; `get` also carries its `etag` |
| `create(**fields)` | a new profile; unset fields take the workspace's defaults |
| `update(profile_or_id, **fields)` | change only the fields given |
| `delete(id)` / `restore(id)` | to the trash and back |
| `clone(id)` | a copy |
| `launch(id)` | start its browser here → `Launch` |
| `devtools(launch)` | wait for the browser's CDP endpoint → `DevTools` |
| `stop(launch)` | close the browser and wait until the app has stopped the profile |
| `running(id)` | context manager: launch, yield `DevTools`, stop — even if the block raised |
| `folders()` / `create_folder(name)` / `delete_folder(id)` | folders |

## Create

```python
from wily_client import ProfileOs, WebrtcMode, Wily

with Wily.connect() as wily:
    proxy = wily.proxies.find('de-1')
    profile = wily.profiles.create(
        name='shop-de-1', os=ProfileOs.WINDOWS11, proxy_id=proxy.id, webrtc=WebrtcMode.PROXY,
        tags=['shop'], start_url='https://wily.bot/', launch_args=['--start-maximized'],
    )
```

Checked by pydantic before sending (`ProfileDraft`, `ProfileChanges`):

| field | rule |
|---|---|
| `os` | `macos`, `windows11`, `windows10`, `linux` |
| `webrtc` | `proxy` (WebRTC shows the proxy's exit), `off`, `real` |
| `proxy_id`, `folder_id` | a UUID |
| `start_url` | http:// or https:// only |
| `timezone` | an IANA name, `Europe/Berlin` |
| `locale` | `de`, `de-DE` |
| `launch_args` | at most 50 switches like `--start-maximized`, each ≤ 200 characters; switches wily sets itself or that open the browser to others (`--remote-debugging-*`, `--proxy-*`, `--user-data-dir`, `--headless`, `--user-agent`, `--lang`, …) are refused |
| `bookmarks` | at most 500 `{url, title, folder}` |
| unknown field | refused |

## Change without losing someone else's change

A profile can be edited from several devices. Pass the `Profile` you read to `update`, and the app refuses the write
(`ConflictError`) if the profile changed since:

```python
current = wily.profiles.get(profile_id)
try:
    wily.profiles.update(current, notes='warmed up')
except ConflictError:
    ...  # read it again, merge, retry
```

`update(profile_id, …)` with a bare id writes unconditionally.

## Launch, drive with Playwright, stop

Three steps — a browser window opens on this machine, Playwright drives it over CDP, the profile stops:

```python
launch = wily.profiles.launch(profile.id)   # 1. the app starts the browser through the profile's proxy
try:
    devtools = wily.profiles.devtools(launch)   # 2. its CDP endpoint, once the browser has opened it
    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(devtools.http_url)
        page = browser.contexts[0].new_page()   # the profile's own context: its cookies and proxy
        page.goto('https://wily.bot/')
finally:
    wily.profiles.stop(launch)                  # 3. close the browser, wait until the profile is stopped
```

Or in one block, stopping on the way out whatever happens inside:

```python
with wily.profiles.running(profile.id) as devtools, sync_playwright() as pw:
    page = pw.chromium.connect_over_cdp(devtools.http_url).contexts[0].new_page()
    page.goto('https://wily.bot/')
```

**Stopping.** The app has no stop operation yet, so `stop` does what closing the window does: it sends the browser
CDP `Browser.close`, Chromium writes its cookies and exits, and the app saves the profile's state and releases its
session; `stop` returns once the app reports the profile stopped. Playwright's own `browser.close()` is **not** a
stop: on a browser it did not start, it only disconnects, and the window stays open.

**What a page can see.** Driving a browser over CDP is visible to a page unless the core hides it, and wily.bot
checks exactly this (measured on wily.bot, 24.11.2026):

| core | what a page sees |
|---|---|
| stock Chromium / Chrome for Testing (`cft-…`) | `navigator.webdriver` is `true` — the app starts the browser with `--remote-debugging-port=0`, which stock Chromium treats as ChromeDriver mode; Playwright's `Runtime.enable` shows in the window and in workers; verdict «automated» |
| wily's Chromium (`chromium-159`) | none of the above: connecting, `goto` and `evaluate` leave no automation finding |

Input still shows on every core today: a CDP click into a cross-site frame and Playwright's scroll-into-view are
told apart from a hand (medium findings; being closed in wily's core). Use the stock core for tests, wily's core for
work, and check with `launch.warnings` which one actually started — a profile whose core is not installed runs on
another one.

- Connect with `connect_over_cdp`, not Playwright's own `launch`: that one adds its own switches and is detectable.
- Open your own tab (`context.new_page()`) rather than `context.pages[0]`: Chromium 159 lists browser-UI targets
  (`chrome://omnibox-popup…`) among the pages.

`launch` needs a signed-in app and an installed browser core for this OS (`wily cores install <id>`); otherwise it
raises `ConflictError` naming what is missing. A profile running on another device raises `ConflictError`
(`profile_in_use`). `launch.warnings` lists what the app adjusted. Closing the browser window ends the profile's
session; the app saves its cookies.

`Launch`: `profile_id`, `core`, `pid`, `executable`, `user_data_dir`, `session_id`, `warnings`.
`DevTools`: `port`, `http_url` (Playwright `connect_over_cdp`, Puppeteer `browserURL`), `ws_url`.

Full scripts: [examples/launch_playwright.py](examples/launch_playwright.py) (the three steps) and
[examples/launch_playwright_short.py](examples/launch_playwright_short.py) (`running`). Both were run against
`wily serve` 0.1.6 on macOS with a signed-in account (24.11.2026).
