"""How a running app can be reached: the doors it lists in its discovery file."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from wily_client.common.domains.model import ValueObject


class DoorKind(StrEnum):
    UNIX_SOCKET = 'unix_socket'
    NAMED_PIPE = 'named_pipe'
    TCP = 'tcp'


class Door(ValueObject):
    """One way in. A socket or pipe needs no token: the OS lets only this user connect."""

    kind: DoorKind
    address: str
    token: str | None = Field(default=None, repr=False)

    @property
    def base_url(self) -> str:
        if self.kind is DoorKind.TCP:
            return f'http://{self.address}'
        # Over a socket or a pipe any host name works; `localhost` is what the app's own docs use.
        return 'http://localhost'


class Discovery(ValueObject):
    """`<data dir>/desktop.json`, written by the desktop app or `wily serve` while it runs."""

    pid: int = 0
    app: str = 'wily'
    app_version: str = ''
    socket: str | None = None
    port: int | None = None
    token: str | None = Field(default=None, repr=False)
