# Connecting to the app

`Wily.connect()` finds the running app by itself. This page says how, for when it does not.

## The discovery file

While the desktop app or `wily serve` runs, it writes `desktop.json` into its data directory and removes it on exit:

| OS | discovery file |
|---|---|
| macOS | `~/Library/Application Support/bot.wily.wily/desktop.json` |
| Windows | `%APPDATA%\wily\wily\data\desktop.json` |
| Linux | `$XDG_DATA_HOME/wily/desktop.json`, else `~/.local/share/wily/desktop.json` |

`WILY_DATA_DIR` moves the whole data directory, for the app and for the library alike: a second app instance, a
test, a container. `Wily.connect('/some/dir')` reads `/some/dir/desktop.json` instead.

No file → `UnavailableError`: the app is not running. A file left by a crash → `UnavailableError` on the first
call: nothing answers at its door.

## Doors

The file lists the doors the app opened, and the library picks the first it can use:

| door | when | token |
|---|---|---|
| Unix socket (`socket`: a path) | macOS, Linux — the default | none: the socket is `0600`, only your user connects |
| named pipe (`socket`: `\\.\pipe\wily-<user>`) | Windows — the default | none: the pipe's ACL admits only your user |
| TCP on `127.0.0.1` (`port`, `token`) | only after `wily settings set api_tcp true` | `Authorization: Bearer <token>`, sent for you |

`wily.door` tells which one was used. TCP is for debugging: any local process, a browser page included, can reach
a port, so leave it off otherwise.

Explicit doors, skipping the file:

```python
Wily.connect(socket='/tmp/wily.sock')            # a Unix socket
Wily.connect(socket=r'\\.\pipe\wily-me')         # a Windows pipe
Wily.connect(port=48123, token='…')              # the debug TCP door
```

## Timeouts

Ordinary calls wait 30 s; `launch` waits up to 10 minutes, because the app may first download a browser core.
Pass `timeout=httpx.Timeout(…)` to `Wily.connect` to change the default.

## Under the hood

The library is an `httpx` client. On a socket it uses `httpx.HTTPTransport(uds=…)`; on Windows a small transport
(`NamedPipeTransport`) feeds httpcore a pipe opened with overlapped I/O from the standard library — the same calls
`multiprocessing` uses — so there is no `pywin32` dependency and timeouts work. Each answer is the JSON of the
matching `wily … --json` command; the local API's own schema is at `wily.app.openapi()` (apps after 0.1.6).
