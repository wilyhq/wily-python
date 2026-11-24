# Examples

Each script is self-contained: its first lines declare the Python it needs and its dependencies
([inline script metadata, PEP 723](https://peps.python.org/pep-0723/)), so [uv](https://docs.astral.sh/uv/)
runs it in one command and installs what it needs on the way — no virtualenv, no `pip install`:

```sh
uv run docs/examples/quickstart.py
uv run docs/examples/launch_playwright.py "shop-de-1"
```

The same on macOS, Linux and Windows (PowerShell: `uv run docs\examples\quickstart.py`). A script can also be run
straight from GitHub, without cloning the repository:

```sh
uv run https://raw.githubusercontent.com/wilyhq/wily-python/main/docs/examples/quickstart.py
```

## What you need

- **uv** — https://docs.astral.sh/uv/getting-started/installation/. uv also fetches the interpreter if you have
  none that fits.
- **Python 3.11 or newer** — what the scripts declare (`requires-python = ">=3.11"`), the same as the library.
- **The wily app running** — the desktop app, or `wily serve` ([install](../install.md)). The scripts talk to it;
  they do not start it.
- **A signed-in app** for everything but `quickstart.py` and `sign_in.py`: proxies and profiles belong to an
  account. `wily login`, or `sign_in.py`.
- The Playwright scripts need **no `playwright install`**: they drive the profile's own browser, which the app
  starts.

The scripts install `wily-client` from this repository's `main` branch. To fix a version, change the line in the
script's header to `"wily-client @ git+https://github.com/wilyhq/wily-python@v0.1.0"`.

## The scripts

| script | shows | arguments |
|---|---|---|
| [quickstart.py](quickstart.py) | the app is running and answering: its version, the way it was reached (Unix socket or named pipe), who is signed in | — |
| [sign_in.py](sign_in.py) | signing a machine in with a device code: prints a link and a code, waits until you confirm — for a headless box or an agent | — |
| [proxies.py](proxies.py) | proxies: a draft validated by pydantic before sending, a check before saving, create, change one field, list, delete, import a pasted list | — |
| [profiles.py](profiles.py) | profiles: a folder, a profile with a proxy, an update that refuses to overwrite a change made elsewhere (ETag), list by tag, clone, trash, restore | — |
| [launch_playwright.py](launch_playwright.py) | launching a profile, connecting Playwright to its browser over CDP, stopping it — the three steps one by one | profile name |
| [launch_playwright_short.py](launch_playwright_short.py) | the same in one `with wily.profiles.running(...)` block, which stops the profile on the way out | profile name |
| [attach_running.py](attach_running.py) | a profile already running (started from the app's window or another script): its CDP endpoint, its proxy both ways — the app's local forwarder and the provider's address with the session filled in — Playwright, and stopping it with `--stop` | profile name, `[--stop]` |

`proxies.py` and `profiles.py` create and delete real records in your account: read them before running.

## Against a local checkout

When you change the library and want an example to use your working copy instead of GitHub, from the repository
root:

```sh
uv run --with-editable . docs/examples/quickstart.py
```
