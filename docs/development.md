# Development

Every gate runs through `make`, the same on macOS, Linux and Windows. The only tools are **GNU make** and
**[uv](https://docs.astral.sh/uv/)** — uv brings Python and every linter at the versions pinned in `uv.lock`.

## Set up

| OS | make | uv |
|---|---|---|
| macOS | comes with Xcode Command Line Tools (`xcode-select --install`) | `brew install uv` |
| Linux | `apt install make` / `dnf install make` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Windows | Git Bash, plus `choco install make` (or `winget install GnuWin32.Make`) | `winget install astral-sh.uv` |

On Windows run the targets from **Git Bash**: the recipes are POSIX shell lines.

```sh
git clone https://github.com/wilyhq/wily-python && cd wily-python
make sync          # .venv with the library and the dev tools
make check         # everything a change must pass
```

## Targets

`make help` lists them.

| target | runs |
|---|---|
| `make sync` | `uv sync`: the library (editable) and the dev group |
| `make lint` | `ruff check`, `ruff format --check`, then `typecheck`, `imports`, `complexity` |
| `make typecheck` | `ty check` over `src`, `tests` and `docs/examples`, at Python 3.11 rules |
| `make imports` | `lint-imports`: the layers of [architecture/OVERVIEW.md](architecture/OVERVIEW.md) |
| `make complexity` | `complexipy`: no function above 15 |
| `make format` | `ruff check --fix` and `ruff format` |
| `make test` | pytest against a fake app behind this OS's own door, and behind TCP |
| `make test-real WILY_BIN=…` | pytest against a real `wily serve` |
| `make examples` | byte-compiles `docs/examples` |
| `make check` | `lint`, `examples`, `test` |
| `make build` | wheel and sdist into `dist/` |
| `make clean` | caches and `dist/` |

`PY=3.11` (any target) runs it on another Python: `make test PY=3.11`.

The linter rules are those of our Python services: `ruff.toml` with the same rule set,
single quotes and 128 columns; `ty`; `import-linter` contracts; `complexipy` at 15; tools pinned in
`pyproject.toml`, and `exclude-newer = "7 days"` so a release younger than a week is never installed.

## Tests

- **`tests/fake_app.py`** — the app's routes and answers in memory, served over a real door: a Unix socket on
  macOS and Linux, a named pipe on Windows, and TCP with a token on all three. Every test runs once per door, so the
  transport of the OS under test is exercised, not mocked.
- **`tests/test_real_app.py`** (`-m real_app`) — starts a released `wily serve` with its own `WILY_DATA_DIR` and
  talks to it: health, sign-in state, schema, and that account operations ask for a sign-in. No account needed.

```sh
make test-real WILY_BIN=/opt/homebrew/bin/wily          # macOS
make test-real WILY_BIN="C:/Program Files/wily/wily.exe" # Windows, from Git Bash
```

## CI

`.github/workflows/ci.yml`, on every push and pull request:

| job | where |
|---|---|
| `make check` | ubuntu, macOS, Windows × Python 3.11 and 3.14 |
| `make test-real` | macOS and Windows, with the CLI of the latest wily release (Linux has none yet) |

A change is ready when CI is green on all of them.

## A change to the app's API

The answers are the JSON of `wily … --json`; the routes are in the local API's schema (`wily.app.openapi()`), and
the proxy and profile objects are `ProxyOut`/`ProfileOut` of https://api.wily.bot/api/openapi.json. When they change:

1. the domain model in `<context>/domains/` (a new field is optional until every released app sends it);
2. the adapter in `<context>/infrastructure/adapters/local_api.py`;
3. the fake app's answer in `tests/fake_app.py`, and a test;
4. the guide in `docs/` and https://wily.bot/docs/libraries/python/.

## Releasing

1. Bump `version` in `pyproject.toml` and `__version__` in `src/wily_client/__init__.py`.
2. `make check`, push, CI green.
3. `git tag v0.1.1 && git push origin v0.1.1` — installs then pin to `…/wily-python@v0.1.1`.

Publishing to PyPI is not set up yet.
