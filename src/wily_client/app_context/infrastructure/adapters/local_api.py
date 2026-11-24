from __future__ import annotations

from typing import TYPE_CHECKING, Any

from wily_client.app_context.domains.value_objects.app import AuthStatus, DeviceCode, Health, User
from wily_client.common.domains.errors import NotFoundError, UnsupportedError

if TYPE_CHECKING:
    from wily_client.common.infrastructure.local_api import LocalApi


class AppLocalApiAdapter:
    def __init__(self, api: LocalApi) -> None:
        self._api = api

    def health(self) -> Health:
        return Health.model_validate(self._api.call('GET', '/v1/health'))

    def auth_status(self) -> AuthStatus:
        d = self._api.call('GET', '/v1/auth/status')
        return AuthStatus.model_validate({**d, 'raw': d})

    def whoami(self) -> User:
        d = self._api.call('GET', '/v1/auth/whoami')
        return User.model_validate(d.get('user', d))

    def login_device(self) -> DeviceCode:
        return DeviceCode.model_validate(self._api.call('POST', '/v1/auth/device'))

    def logout(self) -> None:
        self._api.call('POST', '/v1/auth/logout')

    def openapi(self) -> dict[str, Any]:
        try:
            return self._api.call('GET', '/openapi.json')
        except NotFoundError as e:
            raise UnsupportedError('this app has no /openapi.json: update it past 0.1.6', status=404) from e
