# wily-client documentation

Using the library:

1. [Install](install.md) — the library, and the app it talks to.
2. [Connecting](connecting.md) — how `Wily.connect()` finds the app on macOS, Windows and Linux.
3. [Proxies](proxies.md) — `wily.proxies`.
4. [Profiles](profiles.md) — `wily.profiles`: folders, safe updates, launching, Playwright.
5. [Errors](errors.md) — one class per error code, and what each asks of you.
6. [Examples](examples/) — scripts to copy:

   | script | shows |
   |---|---|
   | [quickstart.py](examples/quickstart.py) | is the app running, who is signed in |
   | [sign_in.py](examples/sign_in.py) | device-code sign-in for a headless box or an agent |
   | [proxies.py](examples/proxies.py) | create, check, change, list, delete, import |
   | [profiles.py](examples/profiles.py) | folders, create with a proxy, update with ETag, clone, trash |
   | [launch_playwright.py](examples/launch_playwright.py) | launch a profile, drive it with Playwright over CDP, stop it |
   | [attach_running.py](examples/attach_running.py) | a profile already running: its CDP endpoint and proxy, Playwright, stop |
   | [launch_playwright_short.py](examples/launch_playwright_short.py) | the same in one `with wily.profiles.running(...)` block |

Working on the library:

- [Development](development.md) — every gate through `make`, on all three OSes; CI; releasing.
- [Architecture](architecture/OVERVIEW.md) — contexts, layers, ports and adapters, and the checks that hold them.
