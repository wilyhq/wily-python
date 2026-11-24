# CLAUDE.md

Rules for agents and people working on `wily-client`, the public Python library for the wily desktop app.
This repository is **public**: nothing private goes into code, docs, commits or issues — no internal hosts,
GitLab paths, customer names or tokens.

## Where things are

- `docs/` — the user guides and `docs/examples/`; `docs/development.md` — the gates; `docs/architecture/OVERVIEW.md`
  — where code goes. **Read OVERVIEW before adding a module**: the layer decides where it lives.
- `src/wily_client/` — contexts `app_context`, `proxy_context`, `profile_context`, shared kernel `common`,
  composition root `client.py`.
- `tests/fake_app.py` — the fake app every test talks to through a real door.

## Gates

`make check` before every push; CI repeats it on Linux, macOS and Windows. No `# noqa`/`# ty: ignore` without the
reason on the same line. A new public name goes into `wily_client/__init__.py` and `__all__`.

## Three operating systems

Everything must work on macOS, Windows and Linux. Before using a path, a socket, a process call or a shell command,
ask what it does on the other two. Windows code is guarded with `if sys.platform == 'win32'` (`make typecheck` checks the
branches of all three OSes from any machine). Makefile recipes stay POSIX shell, run from Git Bash on Windows.

## Validation is pydantic's

Rules on values a script sends live on the DTO as pydantic constraints and validators — not in applications, not
in adapters. A rule copied from the app (launch switches) names its source.

## Docs move with the code

A change to the public API changes, in the same commit: the guide in `docs/`, the example, and the matching page of
https://wily.bot/docs/libraries/python/ (kept in the wily site's sources).
