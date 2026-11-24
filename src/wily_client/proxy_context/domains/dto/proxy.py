"""What a script sends to create or change a proxy. Pydantic checks every value before the call goes out."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, HttpUrl, StringConstraints

from wily_client.common.domains.model import DataTransferObject
from wily_client.proxy_context.domains.constants.proxy import ProxyKind, ProxyProtocol

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Host = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=253, pattern=r'^[^\s/:@]+$')]
Port = Annotated[int, Field(ge=1, le=65535)]
Country = Annotated[str, StringConstraints(strip_whitespace=True, to_upper=True, pattern=r'^[A-Za-z]{2}$')]
Secret = Annotated[str, StringConstraints(max_length=1000)]


class ProxyDraft(DataTransferObject):
    """A new proxy (`ProxyIn` of https://api.wily.bot/api/openapi.json).

    `{session}` in the login or password is kept as written.
    """

    name: Name
    protocol: ProxyProtocol
    host: Host
    port: Port
    username: Secret | None = None
    password: Secret | None = Field(default=None, repr=False)
    kind: ProxyKind | None = None
    country: Country | None = None
    rotate_url: HttpUrl | None = None
    notes: str | None = None


class ProxyChanges(DataTransferObject):
    """A change: only the fields set here are sent, the rest stay as they are."""

    name: Name | None = None
    protocol: ProxyProtocol | None = None
    host: Host | None = None
    port: Port | None = None
    username: Secret | None = None
    password: Secret | None = Field(default=None, repr=False)
    kind: ProxyKind | None = None
    country: Country | None = None
    rotate_url: HttpUrl | None = None
    notes: str | None = None


class ProxyImport(DataTransferObject):
    """A pasted list, one proxy per line. `dry_run=True` only parses and reports."""

    text: Annotated[str, StringConstraints(min_length=1)]
    dry_run: bool = True
