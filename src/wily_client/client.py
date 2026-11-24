"""The composition root: finds the running app, opens its door, wires each context to its adapter."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from wily_client.app_context.applications.app import AppApplication
from wily_client.app_context.infrastructure.adapters.local_api import AppLocalApiAdapter
from wily_client.common.domains.door import Door, DoorKind
from wily_client.common.infrastructure.data_dir import discovery_path
from wily_client.common.infrastructure.discovery_file import read_discovery
from wily_client.common.infrastructure.local_api import DEFAULT_TIMEOUT, LocalApi
from wily_client.common.services.choose_door import choose_door, is_pipe_name
from wily_client.profile_context.applications.profile import ProfileApplication
from wily_client.profile_context.infrastructure.adapters.devtools_file import DevToolsFileAdapter
from wily_client.profile_context.infrastructure.adapters.devtools_socket import DevToolsSocketAdapter
from wily_client.profile_context.infrastructure.adapters.local_api import ProfileLocalApiAdapter
from wily_client.proxy_context.applications.proxy import ProxyApplication
from wily_client.proxy_context.infrastructure.adapters.local_api import ProxyLocalApiAdapter

if TYPE_CHECKING:
    from types import TracebackType

    import httpx


class Wily:
    """The wily desktop app (or `wily serve`) on this machine.

    ```python
    with Wily.connect() as wily:
        print(wily.app.health())
        for proxy in wily.proxies.list():
            print(proxy.name, proxy.alive)
    ```
    """

    def __init__(
        self, door: Door, *, timeout: httpx.Timeout = DEFAULT_TIMEOUT, transport: httpx.BaseTransport | None = None
    ) -> None:
        self._api = LocalApi(door, timeout=timeout, transport=transport)
        self.door = door
        self.app = AppApplication(AppLocalApiAdapter(self._api))
        self.proxies = ProxyApplication(ProxyLocalApiAdapter(self._api))
        self.profiles = ProfileApplication(ProfileLocalApiAdapter(self._api), DevToolsFileAdapter(), DevToolsSocketAdapter())

    @classmethod
    def connect(
        cls,
        data_dir: str | Path | None = None,
        *,
        socket: str | None = None,
        port: int | None = None,
        token: str | None = None,
        timeout: httpx.Timeout = DEFAULT_TIMEOUT,
    ) -> Wily:
        """Finds the app through `desktop.json` (or `WILY_DATA_DIR`), or takes an explicit door.

        `socket` is a Unix socket path or a Windows pipe name; `port` with `token` is the debug TCP door.
        """
        if socket:
            kind = DoorKind.NAMED_PIPE if is_pipe_name(socket) else DoorKind.UNIX_SOCKET
            return cls(Door(kind=kind, address=socket), timeout=timeout)
        if port:
            return cls(Door(kind=DoorKind.TCP, address=f'127.0.0.1:{port}', token=token), timeout=timeout)
        path = discovery_path(Path(data_dir) if data_dir else None)
        return cls(choose_door(read_discovery(path)), timeout=timeout)

    def close(self) -> None:
        self._api.close()

    def __enter__(self) -> Wily:
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None) -> None:
        self.close()
