from __future__ import annotations

from typing import TYPE_CHECKING, Any

from wily_client.common.domains.errors import NotFoundError
from wily_client.proxy_context.domains.dto.proxy import ProxyChanges, ProxyDraft, ProxyImport

if TYPE_CHECKING:
    import builtins

    from wily_client.proxy_context.applications.gateway import ProxyGateway
    from wily_client.proxy_context.domains.entities.proxy import Proxy
    from wily_client.proxy_context.domains.value_objects.proxy_check import ProxyCheck


class ProxyApplication:
    """`wily.proxies`: the workspace's proxies, through the app (the app keeps them on api.wily.bot).

    Every method takes either a DTO or its fields as keywords: `create(ProxyDraft(...))` and
    `create(name=..., protocol=..., ...)` are the same call, and both are validated before anything is sent.
    """

    def __init__(self, gateway: ProxyGateway) -> None:
        self._gateway = gateway

    def list(self) -> builtins.list[Proxy]:
        return self._gateway.list()

    def get(self, proxy_id: str) -> Proxy:
        return self._gateway.get(proxy_id)

    def find(self, name: str) -> Proxy:
        """The one proxy with this exact name."""
        found = [p for p in self._gateway.list() if p.name == name]
        if len(found) != 1:
            raise NotFoundError(f'{len(found)} proxies are named {name!r}')
        return found[0]

    def create(self, draft: ProxyDraft | None = None, **fields: Any) -> Proxy:
        return self._gateway.create(draft or ProxyDraft(**fields))

    def update(self, proxy_id: str, changes: ProxyChanges | None = None, **fields: Any) -> Proxy:
        return self._gateway.update(proxy_id, changes or ProxyChanges(**fields))

    def delete(self, proxy_id: str) -> None:
        self._gateway.delete(proxy_id)

    def check(self, proxy_id: str) -> ProxyCheck:
        """Checks a saved proxy from the server: exit IP, country, latency."""
        return self._gateway.check(proxy_id)

    def check_draft(self, draft: ProxyDraft | None = None, **fields: Any) -> ProxyCheck:
        """Checks a proxy before saving it."""
        return self._gateway.check_draft(draft or ProxyDraft(**fields))

    def import_text(self, text: str, *, dry_run: bool = True) -> dict[str, Any]:
        """Imports a pasted list. The default only parses: pass `dry_run=False` to save."""
        return self._gateway.import_text(ProxyImport(text=text, dry_run=dry_run))
