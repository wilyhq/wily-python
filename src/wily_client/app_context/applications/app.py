from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from wily_client.common.domains.errors import DeniedError

if TYPE_CHECKING:
    from wily_client.app_context.applications.gateway import AppGateway
    from wily_client.app_context.domains.value_objects.app import AuthStatus, DeviceCode, Health, User


class AppApplication:
    """`wily.app`: the app itself and the sign-in on this machine."""

    def __init__(self, gateway: AppGateway) -> None:
        self._gateway = gateway

    def health(self) -> Health:
        return self._gateway.health()

    def auth_status(self) -> AuthStatus:
        return self._gateway.auth_status()

    def whoami(self) -> User:
        return self._gateway.whoami()

    def login_device(self) -> DeviceCode:
        """Starts a device-code sign-in. Show the person the link and code; `wait_signed_in` waits for it."""
        return self._gateway.login_device()

    def wait_signed_in(self, timeout: float = 600.0, interval: float = 2.0) -> AuthStatus:
        deadline = time.monotonic() + timeout
        while True:
            status = self._gateway.auth_status()
            if status.signed_in:
                return status
            if status.device_login_state in {'denied', 'expired', 'failed'}:
                raise DeniedError(f'device sign-in ended: {status.device_login_state}')
            if time.monotonic() >= deadline:
                raise DeniedError('device sign-in was not confirmed in time')
            time.sleep(interval)

    def logout(self) -> None:
        self._gateway.logout()

    def openapi(self) -> dict[str, Any]:
        """The local API's own OpenAPI schema (apps after 0.1.6)."""
        return self._gateway.openapi()
