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

## Launch and drive

```python
launch = wily.profiles.launch(profile.id)   # the app starts the browser through the profile's proxy
devtools = wily.profiles.devtools(launch)   # waits for the browser's DevToolsActivePort

from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    browser = pw.chromium.connect_over_cdp(devtools.http_url)
    page = browser.contexts[0].new_page()
    page.goto('https://wily.bot/')
```

`launch` needs a signed-in app and an installed browser core for this OS (`wily cores install <id>`); otherwise it
raises `ConflictError` naming what is missing. A profile running on another device raises `ConflictError`
(`profile_in_use`). `launch.warnings` lists what the app adjusted. Closing the browser window ends the profile's
session; the app saves its cookies.

`Launch`: `profile_id`, `core`, `pid`, `executable`, `user_data_dir`, `session_id`, `warnings`.
`DevTools`: `port`, `http_url` (Playwright `connect_over_cdp`, Puppeteer `browserURL`), `ws_url`.

Full script: [examples/launch_playwright.py](examples/launch_playwright.py).
