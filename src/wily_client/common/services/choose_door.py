"""Which door to use: the socket (or pipe) when the app opened one, TCP with its token otherwise."""

from __future__ import annotations

from wily_client.common.domains.door import Discovery, Door, DoorKind
from wily_client.common.domains.errors import UnavailableError


def is_pipe_name(address: str) -> bool:
    return address.startswith(('\\\\.\\pipe\\', '//./pipe/'))


def choose_door(discovery: Discovery) -> Door:
    if discovery.socket:
        kind = DoorKind.NAMED_PIPE if is_pipe_name(discovery.socket) else DoorKind.UNIX_SOCKET
        return Door(kind=kind, address=discovery.socket)
    if discovery.port and discovery.token:
        return Door(kind=DoorKind.TCP, address=f'127.0.0.1:{discovery.port}', token=discovery.token)
    raise UnavailableError(f'{discovery.app} (pid {discovery.pid}) lists no door this client can open')
