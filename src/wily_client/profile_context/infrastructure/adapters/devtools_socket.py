"""One CDP command to a browser, over its DevTools WebSocket — standard library only.

The app has no «stop» route yet, so a profile is stopped the way a person stops it: its browser is
closed, here with `Browser.close`, which lets Chromium write its cookies before exiting. Pulling in a
WebSocket library for one frame is not worth a dependency: the handshake and one masked text frame are
all it takes.
"""

from __future__ import annotations

import base64
import json
import os
import socket
from contextlib import suppress
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from wily_client.profile_context.domains.value_objects.profile import DevTools

OPCODE_TEXT = 0x81
MASKED = 0x80
SHORT_LIMIT = 126
EXTENDED_16 = 126
EXTENDED_64 = 127
MAX_16 = 0xFFFF


def _frame(payload: bytes) -> bytes:
    key = os.urandom(4)
    size = len(payload)
    if size < SHORT_LIMIT:
        head = bytes([OPCODE_TEXT, MASKED | size])
    elif size <= MAX_16:
        head = bytes([OPCODE_TEXT, MASKED | EXTENDED_16]) + size.to_bytes(2, 'big')
    else:
        head = bytes([OPCODE_TEXT, MASKED | EXTENDED_64]) + size.to_bytes(8, 'big')
    return head + key + bytes(b ^ key[i % 4] for i, b in enumerate(payload))


class DevToolsSocketAdapter:
    def send(self, devtools: DevTools, method: str, timeout: float = 10.0) -> None:
        url = urlsplit(devtools.ws_url)
        with socket.create_connection(('127.0.0.1', devtools.port), timeout=timeout) as sock:
            key = base64.b64encode(os.urandom(16)).decode()
            sock.sendall(
                f'GET {url.path} HTTP/1.1\r\nHost: 127.0.0.1:{devtools.port}\r\nUpgrade: websocket\r\n'
                f'Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n'.encode()
            )
            answer = b''
            while b'\r\n\r\n' not in answer:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                answer += chunk
            if b' 101 ' not in answer.split(b'\r\n', 1)[0]:
                raise ConnectionError(f'DevTools refused the WebSocket: {answer[:80]!r}')
            sock.sendall(_frame(json.dumps({'id': 1, 'method': method}).encode()))
            with suppress(OSError):  # the browser answers, or just closes the connection as it exits
                sock.recv(4096)
