"""A fake wily app: the local API's routes and answers, kept in memory, behind a real door.

The same handler serves three doors — TCP with a token, a Unix socket, a Windows named pipe — so the
tests run the library's real transport for the OS they run on. Answers copy the app's shapes
(the JSON of `wily … --json`, see `wily.app.openapi()`).
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import socketserver
import sys
import threading
import uuid
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import parse_qs, urlsplit

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

NOW = '2026-11-24T10:00:00Z'
# Not exported by `_winapi`: byte mode is the zero flag of CreateNamedPipe.
PIPE_TYPE_BYTE = 0
PIPE_READMODE_BYTE = 0
Answer = tuple[int, dict[str, Any]]


def err(status: int, code: str, exit_code: int, message: str) -> Answer:
    return status, {'error': {'code': code, 'exit_code': exit_code, 'message': message}}


class FakeApp:
    def __init__(self, user_data_root: Path) -> None:
        self.proxies: dict[str, dict[str, Any]] = {}
        self.profiles: dict[str, dict[str, Any]] = {}
        self.folders: dict[str, dict[str, Any]] = {}
        self.requests: list[tuple[str, str, dict[str, str], Any]] = []
        self.signed_in = True
        self.user_data_root = user_data_root
        self.lock = threading.Lock()
        self.routes: list[tuple[str, re.Pattern[str], Callable[..., Answer]]] = [
            (m, re.compile(f'^{p}$'), h)
            for m, p, h in [
                ('GET', '/v1/health', self.health),
                ('GET', '/openapi.json', self.openapi),
                ('GET', '/v1/auth/status', self.auth_status),
                ('GET', '/v1/auth/whoami', self.whoami),
                ('GET', '/v1/proxies', self.proxies_list),
                ('POST', '/v1/proxies', self.proxies_create),
                ('POST', '/v1/proxies/check', self.proxies_check_draft),
                ('POST', '/v1/proxies/import', self.proxies_import),
                ('GET', '/v1/proxies/(?P<id>[^/]+)', self.proxies_get),
                ('PATCH', '/v1/proxies/(?P<id>[^/]+)', self.proxies_update),
                ('DELETE', '/v1/proxies/(?P<id>[^/]+)', self.proxies_delete),
                ('POST', '/v1/proxies/(?P<id>[^/]+)/check', self.proxies_check),
                ('GET', '/v1/profiles', self.profiles_list),
                ('POST', '/v1/profiles', self.profiles_create),
                ('GET', '/v1/profiles/(?P<id>[^/]+)', self.profiles_get),
                ('PATCH', '/v1/profiles/(?P<id>[^/]+)', self.profiles_update),
                ('DELETE', '/v1/profiles/(?P<id>[^/]+)', self.profiles_delete),
                ('POST', '/v1/profiles/(?P<id>[^/]+)/restore', self.profiles_restore),
                ('POST', '/v1/profiles/(?P<id>[^/]+)/clone', self.profiles_clone),
                ('POST', '/v1/profiles/(?P<id>[^/]+)/launch', self.profiles_launch),
                ('GET', '/v1/profile-folders', self.folders_list),
                ('POST', '/v1/profile-folders', self.folders_create),
            ]
        ]

    # --- dispatch ---------------------------------------------------------------------------

    def handle(self, method: str, target: str, headers: dict[str, str], body: bytes) -> Answer:
        url = urlsplit(target)
        payload = json.loads(body) if body else None
        query = {k: v[0] for k, v in parse_qs(url.query).items()}
        with self.lock:
            self.requests.append((method, target, headers, payload))
            for m, pattern, handler in self.routes:
                if m == method and (match := pattern.match(url.path)):
                    return handler(payload=payload, query=query, headers=headers, **match.groupdict())
        return 404, {}

    # --- app --------------------------------------------------------------------------------

    def health(self, **_: Any) -> Answer:
        return 200, {'app': 'wily', 'version': '0.1.7', 'pid': 4242}

    def openapi(self, **_: Any) -> Answer:
        return 200, {'openapi': '3.1.0', 'info': {'title': 'wily local API', 'version': '0.1.7'}, 'paths': {}}

    def auth_status(self, **_: Any) -> Answer:
        return 200, {'signed_in': self.signed_in, 'issuer': 'https://api.wily.bot', 'device': None}

    def whoami(self, **_: Any) -> Answer:
        if not self.signed_in:
            return err(401, 'auth_required', 3, 'not signed in: `wily login`')
        return 200, {'user': {'sub': 'u1', 'email': 'someone@example.com', 'name': 'Someone'}}

    # --- proxies ----------------------------------------------------------------------------

    def _proxy(self, body: dict[str, Any], proxy_id: str | None = None) -> dict[str, Any]:
        return {
            'id': proxy_id or str(uuid.uuid4()),
            'name': body['name'],
            'protocol': body['protocol'],
            'host': body['host'],
            'port': body['port'],
            'username': body.get('username'),
            'password': body.get('password'),
            'has_password': bool(body.get('password')),
            'kind': body.get('kind') or 'unknown',
            'country': body.get('country'),
            'has_rotate_url': bool(body.get('rotate_url')),
            'notes': body.get('notes') or '',
            'last_check': None,
            'profiles_count': 0,
            'usage_30d_bytes': None,
            'created_at': NOW,
            'updated_at': NOW,
            'brand_new_server_field': {'ignored': True},
        }

    def proxies_list(self, **_: Any) -> Answer:
        return 200, {'proxies': list(self.proxies.values())}

    def proxies_create(self, payload: dict[str, Any], **_: Any) -> Answer:
        p = self._proxy(payload)
        self.proxies[p['id']] = p
        return 200, {'proxy': p}

    def proxies_get(self, id: str, **_: Any) -> Answer:  # noqa: A002 — the route's name
        if id not in self.proxies:
            return err(404, 'not_found', 5, f'no proxy {id}')
        return 200, {'proxy': self.proxies[id]}

    def proxies_update(self, id: str, payload: dict[str, Any], **_: Any) -> Answer:  # noqa: A002
        if id not in self.proxies:
            return err(404, 'not_found', 5, f'no proxy {id}')
        self.proxies[id] = self._proxy({**self.proxies[id], **payload}, id)
        return 200, {'proxy': self.proxies[id]}

    def proxies_delete(self, id: str, **_: Any) -> Answer:  # noqa: A002
        if self.proxies.pop(id, None) is None:
            return err(404, 'not_found', 5, f'no proxy {id}')
        return 200, {'deleted': id}

    def _check(self) -> dict[str, Any]:
        return {
            'status': 'ok',
            'exit_ip': '203.0.113.7',
            'exit_country': 'DE',
            'latency_ms': 120,
            'error_code': None,
            'checked_at': NOW,
        }

    def proxies_check(self, id: str, **_: Any) -> Answer:  # noqa: A002
        if id not in self.proxies:
            return err(404, 'not_found', 5, f'no proxy {id}')
        self.proxies[id]['last_check'] = self._check()
        return 200, {'id': id, 'check': self._check()}

    def proxies_check_draft(self, **_: Any) -> Answer:
        return 200, {'check': self._check()}

    def proxies_import(self, payload: dict[str, Any], **_: Any) -> Answer:
        lines = [x for x in payload['text'].splitlines() if x.strip()]
        return 200, {'parsed': len(lines), 'created': 0 if payload.get('dry_run', True) else len(lines)}

    # --- profiles ---------------------------------------------------------------------------

    def _profile(self, body: dict[str, Any]) -> dict[str, Any]:
        proxy = self.proxies.get(body.get('proxy_id') or '')
        return {
            'id': str(uuid.uuid4()),
            'name': body.get('name') or 'Profile 1',
            'folder': None,
            'tags': body.get('tags') or [],
            'notes': body.get('notes') or '',
            'os': body.get('os') or 'macos',
            'core': body.get('core') or 'chromium-stable',
            'proxy': {k: proxy[k] for k in ('id', 'name', 'protocol', 'country')} if proxy else None,
            'geo_from_proxy': True,
            'timezone': body.get('timezone'),
            'locale': body.get('locale'),
            'webrtc': body.get('webrtc') or 'proxy',
            'start_url': body.get('start_url'),
            'bookmarks': body.get('bookmarks') or [],
            'launch_args': body.get('launch_args') or [],
            'state': 'stopped',
            'session': None,
            'pinned': False,
            'version': 1,
            'last_warmup': None,
            'created_at': NOW,
            'updated_at': NOW,
            'deleted_at': None,
        }

    def profiles_list(self, query: dict[str, str], **_: Any) -> Answer:
        trash = query.get('trash') == 'true'
        rows = [p for p in self.profiles.values() if (p['deleted_at'] is not None) == trash]
        if q := query.get('q'):
            rows = [p for p in rows if q.lower() in p['name'].lower()]
        return 200, {'profiles': rows}

    def profiles_create(self, payload: dict[str, Any], **_: Any) -> Answer:
        p = self._profile(payload)
        self.profiles[p['id']] = p
        return 200, {'profile': p}

    def profiles_get(self, id: str, **_: Any) -> Answer:  # noqa: A002
        if id not in self.profiles:
            return err(404, 'not_found', 5, f'no profile {id}')
        p = self.profiles[id]
        return 200, {'profile': p, 'etag': f'"{p["version"]}"'}

    def profiles_update(self, id: str, payload: dict[str, Any], headers: dict[str, str], **_: Any) -> Answer:  # noqa: A002
        p = self.profiles.get(id)
        if p is None:
            return err(404, 'not_found', 5, f'no profile {id}')
        if (tag := headers.get('if-match')) and tag != f'"{p["version"]}"':
            return err(409, 'conflict', 6, 'the profile was changed elsewhere')
        p.update({k: v for k, v in payload.items() if k != 'proxy_id'}, version=p['version'] + 1)
        return 200, {'profile': p, 'etag': f'"{p["version"]}"'}

    def profiles_delete(self, id: str, **_: Any) -> Answer:  # noqa: A002
        self.profiles[id]['deleted_at'] = NOW
        return 200, {'trashed': id}

    def profiles_restore(self, id: str, **_: Any) -> Answer:  # noqa: A002
        self.profiles[id]['deleted_at'] = None
        return 200, {'profile': self.profiles[id]}

    def profiles_clone(self, id: str, **_: Any) -> Answer:  # noqa: A002
        p = {**self.profiles[id], 'id': str(uuid.uuid4()), 'name': self.profiles[id]['name'] + ' (copy)'}
        self.profiles[p['id']] = p
        return 200, {'profile': p}

    def profiles_launch(self, id: str, **_: Any) -> Answer:  # noqa: A002
        p = self.profiles.get(id)
        if p is None:
            return err(404, 'not_found', 5, f'no profile {id}')
        if p['state'] == 'running':
            return err(409, 'conflict', 6, f'profile {id} is already running (pid 777)')
        p['state'] = 'running'
        data_dir = self.user_data_root / id
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / 'DevToolsActivePort').write_text('9333\n/devtools/browser/abc\n', encoding='utf-8')
        launched = {'pid': 777, 'executable': '/cores/chromium/chrome', 'user_data_dir': str(data_dir)}
        return 200, {'profile_id': id, 'core': p['core'], 'launched': launched, 'session_id': 's1', 'warnings': []}

    def folders_list(self, **_: Any) -> Answer:
        return 200, {'folders': list(self.folders.values())}

    def folders_create(self, payload: dict[str, Any], **_: Any) -> Answer:
        f = {'id': str(uuid.uuid4()), 'name': payload['name']}
        self.folders[f['id']] = f
        return 200, {'folder': f}


# --- doors -----------------------------------------------------------------------------------


def _handler(app: FakeApp, token: str | None) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        def _serve(self) -> None:
            length = int(self.headers.get('Content-Length') or 0)
            body = self.rfile.read(length) if length else b''
            headers = {k.lower(): v for k, v in self.headers.items()}
            if token and headers.get('authorization') != f'Bearer {token}':
                status, answer = 401, {}
            else:
                status, answer = app.handle(self.command, self.path, headers, body)
            data = json.dumps(answer).encode() if answer else b''
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        do_GET = do_POST = do_PATCH = do_PUT = do_DELETE = _serve  # noqa: N815 — http.server's names

        def address_string(self) -> str:
            return 'local'

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 — http.server's signature
            del format, args

    return Handler


@dataclass(frozen=True)
class Door:
    """A started door: what goes into `desktop.json`, and how to stop it."""

    discovery: dict[str, Any]
    stop: Callable[[], None]


def serve_tcp(app: FakeApp, token: str) -> Door:
    server = ThreadingHTTPServer(('127.0.0.1', 0), _handler(app, token))
    threading.Thread(target=server.serve_forever, kwargs={'poll_interval': 0.02}, daemon=True).start()

    def stop() -> None:
        server.shutdown()
        server.server_close()

    return Door({'port': server.server_address[1], 'token': token}, stop)


def serve_unix(app: FakeApp, path: str) -> Door:
    if sys.platform == 'win32':
        raise RuntimeError('Unix sockets are served on macOS and Linux only')

    class Server(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
        daemon_threads = True

    server = Server(path, _handler(app, None))
    threading.Thread(target=server.serve_forever, kwargs={'poll_interval': 0.02}, daemon=True).start()

    def stop() -> None:
        server.shutdown()
        server.server_close()

    return Door({'socket': path}, stop)


def serve_pipe(app: FakeApp, name: str) -> Door:
    """A named-pipe server on `_winapi`, one thread per client — like the app's tokio pipe server."""
    if sys.platform != 'win32':
        raise RuntimeError('named pipes exist only on Windows')
    import _winapi  # noqa: PLC0415

    handler = _handler(app, None)
    stopping = threading.Event()

    def create() -> int:
        return _winapi.CreateNamedPipe(
            name,
            _winapi.PIPE_ACCESS_DUPLEX,
            PIPE_TYPE_BYTE | PIPE_READMODE_BYTE | _winapi.PIPE_WAIT,
            _winapi.PIPE_UNLIMITED_INSTANCES,
            65536,
            65536,
            0,
            _winapi.NULL,
        )

    def client(h: int) -> None:
        try:  # one handler per connection: it serves keep-alive requests until the client closes
            handler(cast('Any', _PipeFile(h)), 'local', cast('Any', None))
        except OSError:
            pass
        finally:
            _winapi.CloseHandle(h)

    def accept() -> None:
        while not stopping.is_set():
            h = create()
            try:
                _winapi.ConnectNamedPipe(h, False)
            except OSError:
                _winapi.CloseHandle(h)
                continue
            if stopping.is_set():
                _winapi.CloseHandle(h)
                return
            threading.Thread(target=client, args=(h,), daemon=True).start()

    threading.Thread(target=accept, daemon=True).start()

    def stop() -> None:
        stopping.set()
        with contextlib.suppress(OSError):  # wake the accept loop with one last client
            _winapi.CloseHandle(
                _winapi.CreateFile(name, _winapi.GENERIC_READ, 0, _winapi.NULL, _winapi.OPEN_EXISTING, 0, _winapi.NULL)
            )

    return Door({'socket': name}, stop)


class _PipeFile:
    """What `BaseHTTPRequestHandler` needs from a socket: `makefile` for rfile and wfile."""

    def __init__(self, handle: int) -> None:
        raw = _PipeRaw(handle)
        self.rfile = io.BufferedReader(raw)
        self.wfile = raw

    def makefile(self, mode: str, *args: Any, **kwargs: Any) -> Any:
        del args, kwargs
        return self.rfile if 'r' in mode else self.wfile

    def sendall(self, data: bytes) -> None:
        self.wfile.write(data)

    def settimeout(self, timeout: float | None) -> None:
        del timeout

    def setsockopt(self, *args: Any) -> None:
        del args

    def shutdown(self, how: int) -> None:
        del how

    def close(self) -> None:
        pass


class _PipeRaw(io.RawIOBase):
    def __init__(self, handle: int) -> None:
        super().__init__()
        self._h = handle

    def readable(self) -> bool:
        return True

    def writable(self) -> bool:
        return True

    def readinto(self, buf: Any) -> int:
        if sys.platform != 'win32':
            return 0
        import _winapi  # noqa: PLC0415

        try:
            data, _ = _winapi.ReadFile(self._h, len(buf))
        except OSError:
            return 0  # the client closed its end
        buf[: len(data)] = data
        return len(data)

    def write(self, data: Any) -> int:
        if sys.platform != 'win32':
            return 0
        import _winapi  # noqa: PLC0415

        _winapi.WriteFile(self._h, bytes(data))
        return len(data)
