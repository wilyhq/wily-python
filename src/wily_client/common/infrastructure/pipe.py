"""HTTP over a Windows named pipe for httpx: an httpcore network backend on `_winapi`.

CPython on Windows has no `AF_UNIX` client that the app's pipe would accept, and httpx has no pipe
transport, so the pipe is opened with the same overlapped calls `multiprocessing` uses — standard
library only, with timeouts. The rest of HTTP (framing, keep-alive) is httpcore's, as for any socket.
"""

from __future__ import annotations

import sys
import time
from typing import TYPE_CHECKING, Any, cast

import httpcore
import httpx

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

ERROR_FILE_NOT_FOUND = 2
ERROR_BROKEN_PIPE = 109
ERROR_PIPE_BUSY = 231
ERROR_MORE_DATA = 234
ERROR_PIPE_NOT_CONNECTED = 233
CLOSED = (ERROR_BROKEN_PIPE, ERROR_PIPE_NOT_CONNECTED)
WINDOWS_ONLY = 'named pipes exist only on Windows'

if sys.platform == 'win32':
    import _winapi


def _ms(timeout: float | None) -> int:
    if sys.platform != 'win32':
        raise httpcore.ConnectError(WINDOWS_ONLY)
    return _winapi.INFINITE if timeout is None else max(0, int(timeout * 1000))


class PipeStream(httpcore.NetworkStream):
    def __init__(self, handle: int) -> None:
        self._handle = handle

    def _wait(self, ov: Any, timeout: float | None, on_timeout: type[Exception]) -> int:
        if sys.platform != 'win32':
            raise httpcore.ConnectError(WINDOWS_ONLY)

        if _winapi.WaitForMultipleObjects([ov.event], False, _ms(timeout)) != _winapi.WAIT_OBJECT_0:
            ov.cancel()
            ov.GetOverlappedResult(True)
            raise on_timeout('named pipe timed out')
        done, _ = ov.GetOverlappedResult(True)
        return done

    def read(self, max_bytes: int, timeout: float | None = None) -> bytes:
        if sys.platform != 'win32':
            raise httpcore.ConnectError(WINDOWS_ONLY)

        try:
            ov, err = _winapi.ReadFile(self._handle, max_bytes, overlapped=True)
        except OSError as e:
            if e.winerror in CLOSED:
                return b''
            raise httpcore.ReadError(str(e)) from e
        try:
            if err == _winapi.ERROR_IO_PENDING:
                self._wait(ov, timeout, httpcore.ReadTimeout)
            return bytes(ov.getbuffer() or b'')
        except OSError as e:
            if e.winerror in CLOSED:
                return b''
            if e.winerror == ERROR_MORE_DATA:
                return bytes(ov.getbuffer() or b'')
            raise httpcore.ReadError(str(e)) from e

    def write(self, buffer: bytes, timeout: float | None = None) -> None:
        if sys.platform != 'win32':
            raise httpcore.ConnectError(WINDOWS_ONLY)

        view = memoryview(buffer)
        while view:
            try:
                ov, err = _winapi.WriteFile(self._handle, view, overlapped=True)
                if err == _winapi.ERROR_IO_PENDING:
                    sent = self._wait(ov, timeout, httpcore.WriteTimeout)
                else:
                    sent, _ = ov.GetOverlappedResult(True)
            except OSError as e:
                raise httpcore.WriteError(str(e)) from e
            view = view[sent:]

    def close(self) -> None:
        if sys.platform != 'win32':
            raise httpcore.ConnectError(WINDOWS_ONLY)

        if self._handle:
            _winapi.CloseHandle(self._handle)
            self._handle = 0

    def start_tls(self, *args: Any, **kwargs: Any) -> httpcore.NetworkStream:
        del args, kwargs
        raise httpcore.ConnectError('no TLS over a local pipe')

    def get_extra_info(self, info: str) -> Any:
        del info  # no socket, peer or TLS object behind a pipe
        return None


def open_pipe(name: str, timeout: float | None) -> PipeStream:
    """Opens the client end; a busy pipe (every instance taken) is waited for until `timeout`."""
    if sys.platform != 'win32':
        raise httpcore.ConnectError(WINDOWS_ONLY)

    deadline = None if timeout is None else time.monotonic() + timeout
    while True:
        try:
            handle = _winapi.CreateFile(
                name,
                _winapi.GENERIC_READ | _winapi.GENERIC_WRITE,
                0,
                _winapi.NULL,
                _winapi.OPEN_EXISTING,
                _winapi.FILE_FLAG_OVERLAPPED,
                _winapi.NULL,
            )
            return PipeStream(handle)
        except OSError as e:
            if e.winerror == ERROR_FILE_NOT_FOUND:
                raise httpcore.ConnectError(f'no app listens on {name}') from e
            if e.winerror != ERROR_PIPE_BUSY:
                raise httpcore.ConnectError(str(e)) from e
        left = None if deadline is None else deadline - time.monotonic()
        if left is not None and left <= 0:
            raise httpcore.ConnectTimeout(f'{name} stayed busy')
        _winapi.WaitNamedPipe(name, _ms(min(left, 1.0) if left is not None else 1.0))


class PipeBackend(httpcore.NetworkBackend):
    def __init__(self, name: str) -> None:
        self._name = name

    def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options: Iterable[Any] | None = None,
    ) -> httpcore.NetworkStream:
        del host, port, local_address, socket_options  # the URL's host is a placeholder: the pipe is the address
        return open_pipe(self._name, timeout)

    def connect_unix_socket(
        self, path: str, timeout: float | None = None, socket_options: Iterable[Any] | None = None
    ) -> httpcore.NetworkStream:
        del path, socket_options
        return open_pipe(self._name, timeout)

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)


# httpcore errors → httpx errors, as httpx's own transport maps them.
_MAPPING: tuple[tuple[type[Exception], type[httpx.TransportError]], ...] = (
    (httpcore.ConnectTimeout, httpx.ConnectTimeout),
    (httpcore.ReadTimeout, httpx.ReadTimeout),
    (httpcore.WriteTimeout, httpx.WriteTimeout),
    (httpcore.PoolTimeout, httpx.PoolTimeout),
    (httpcore.ConnectError, httpx.ConnectError),
    (httpcore.ReadError, httpx.ReadError),
    (httpcore.WriteError, httpx.WriteError),
    (httpcore.RemoteProtocolError, httpx.RemoteProtocolError),
)


def _as_httpx(e: Exception) -> Exception:
    for source, target in _MAPPING:
        if isinstance(e, source):
            return target(str(e))
    return e


class _Body(httpx.SyncByteStream):
    def __init__(self, stream: Iterable[bytes]) -> None:
        self._stream = stream

    def __iter__(self) -> Iterator[bytes]:
        try:
            yield from self._stream
        except Exception as e:
            raise _as_httpx(e) from e

    def close(self) -> None:
        close = getattr(self._stream, 'close', None)
        if close:
            close()


class NamedPipeTransport(httpx.BaseTransport):
    """`httpx.Client(transport=NamedPipeTransport(r'\\\\.\\pipe\\wily-me'))` — the pipe's twin of `uds=`."""

    def __init__(self, name: str) -> None:
        self._pool = httpcore.ConnectionPool(network_backend=PipeBackend(name), max_connections=4)

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        req = httpcore.Request(
            method=request.method,
            url=httpcore.URL(
                scheme=request.url.raw_scheme,
                host=request.url.raw_host,
                port=request.url.port,
                target=request.url.raw_path,
            ),
            headers=request.headers.raw,
            content=request.stream,
            extensions=request.extensions,
        )
        try:
            resp = self._pool.handle_request(req)
        except Exception as e:
            raise _as_httpx(e) from e
        return httpx.Response(
            status_code=resp.status,
            headers=resp.headers,
            stream=_Body(cast('Iterable[bytes]', resp.stream)),
            extensions=resp.extensions,
        )

    def close(self) -> None:
        self._pool.close()
