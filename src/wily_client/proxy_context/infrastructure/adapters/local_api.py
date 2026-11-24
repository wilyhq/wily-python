from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from wily_client.proxy_context.domains.entities.proxy import Proxy
from wily_client.proxy_context.domains.value_objects.proxy_check import ProxyCheck

if TYPE_CHECKING:
    import builtins

    from wily_client.common.infrastructure.local_api import LocalApi
    from wily_client.proxy_context.domains.dto.proxy import ProxyChanges, ProxyDraft, ProxyImport


def _path(proxy_id: str, tail: str = '') -> str:
    return f'/v1/proxies/{quote(proxy_id, safe="")}{tail}'


class ProxyLocalApiAdapter:
    def __init__(self, api: LocalApi) -> None:
        self._api = api

    def list(self) -> builtins.list[Proxy]:
        return [Proxy.model_validate(p) for p in self._api.call('GET', '/v1/proxies').get('proxies', [])]

    def get(self, proxy_id: str) -> Proxy:
        return Proxy.model_validate(self._api.call('GET', _path(proxy_id))['proxy'])

    def create(self, draft: ProxyDraft) -> Proxy:
        return Proxy.model_validate(self._api.call('POST', '/v1/proxies', json=draft.to_body())['proxy'])

    def update(self, proxy_id: str, changes: ProxyChanges) -> Proxy:
        return Proxy.model_validate(self._api.call('PATCH', _path(proxy_id), json=changes.to_body())['proxy'])

    def delete(self, proxy_id: str) -> None:
        self._api.call('DELETE', _path(proxy_id))

    def check(self, proxy_id: str) -> ProxyCheck:
        return ProxyCheck.model_validate(self._api.call('POST', _path(proxy_id, '/check'))['check'])

    def check_draft(self, draft: ProxyDraft) -> ProxyCheck:
        return ProxyCheck.model_validate(self._api.call('POST', '/v1/proxies/check', json=draft.to_body())['check'])

    def import_text(self, request: ProxyImport) -> dict[str, Any]:
        return self._api.call('POST', '/v1/proxies/import', json=request.to_body())
