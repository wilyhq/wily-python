# Install

## The library

Python 3.11 or newer, on macOS, Windows or Linux. The library is not on PyPI yet; install it from GitHub:

```sh
pip install "wily-client @ git+https://github.com/wilyhq/wily-python"
# or, in a uv project
uv add "wily-client @ git+https://github.com/wilyhq/wily-python"
```

A fixed version: append `@v0.1.0` (a tag) to the URL. Dependencies: `httpx`, `httpcore` and `pydantic` 2 — nothing
platform-specific; the Windows pipe is opened with the standard library.

## The app it talks to

The library drives a running wily app; it does not contain one. Install it as https://wily.bot/docs/install/ says:

| OS | app |
|---|---|
| macOS (Apple Silicon) | `brew tap wilyhq/tap && brew trust --tap wilyhq/tap && brew install --cask wilyhq/tap/wily` |
| Windows x64 | the zip from https://wily.bot/docs/install/#windows-x64 |
| Linux | no release yet — the library is ready for it (it reads `~/.local/share/wily/desktop.json`) |

Either start the desktop app, or run the same server without a window:

```sh
wily serve
```

Then sign in once (`wily login`, or [sign_in.py](examples/sign_in.py)): proxies and profiles belong to an account.

## Check

```sh
python docs/examples/quickstart.py
```

prints the app's version and the door it went through (`unix_socket` or `named_pipe`), or says the app is not running.
