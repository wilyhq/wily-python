from __future__ import annotations

from datetime import datetime
from urllib.parse import quote

from pydantic import Field

from wily_client.common.domains.model import Entity
from wily_client.proxy_context.domains.constants.proxy import ProxyKind, ProxyProtocol
from wily_client.proxy_context.domains.value_objects.proxy_check import ProxyCheck

SESSION = '{session}'


class Proxy(Entity):
    """A proxy of the workspace (`ProxyOut` of https://api.wily.bot/api/openapi.json).

    `password` is plaintext, as stored — it is hidden from `repr`, and a script must not log a proxy whole.
    """

    name: str
    protocol: ProxyProtocol
    host: str
    port: int
    username: str | None = None
    password: str | None = Field(default=None, repr=False)
    kind: ProxyKind = ProxyKind.UNKNOWN
    country: str | None = None
    notes: str = ''
    last_check: ProxyCheck | None = None
    profiles_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def alive(self) -> bool | None:
        """The last check's verdict; `None` while it was never checked."""
        return None if self.last_check is None else self.last_check.ok

    def url(self, *, with_credentials: bool = True) -> str:
        """`socks5://user:pass@host:port` — for httpx, requests or Playwright's `proxy`.

        A login with `{session}` is a template the server fills per profile; connecting with it as is would land on a
        session nobody else uses — so it raises: take `wily.profiles.proxy(profile_id).upstream` instead.
        """
        auth = ''
        if with_credentials and any(SESSION in (v or '') for v in (self.username, self.password)):
            raise ValueError(
                f'proxy {self.name!r} has {SESSION} in its login, which the server fills per profile: '
                'use wily.profiles.proxy(profile_id).upstream'
            )
        if with_credentials and self.username:
            auth = quote(self.username, safe='')
            if self.password:
                auth += ':' + quote(self.password, safe='')
            auth += '@'
        return f'{self.protocol.value}://{auth}{self.host}:{self.port}'
