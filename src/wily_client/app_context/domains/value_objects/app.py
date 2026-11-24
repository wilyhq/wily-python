"""What the running app says about itself and about the sign-in on this machine."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from wily_client.common.domains.model import ValueObject


class Health(ValueObject):
    app: str
    version: str
    pid: int


class AuthStatus(ValueObject):
    """Read from disk by the app, without a network call (`wily status`)."""

    signed_in: bool
    source: str | None = None
    expires_at: int | None = None
    device_login: dict[str, Any] | None = None
    raw: dict[str, Any] = Field(default_factory=dict, repr=False, exclude=True)

    @property
    def device_login_state(self) -> str | None:
        return (self.device_login or {}).get('state')


class User(ValueObject):
    sub: str = ''
    email: str | None = None
    name: str | None = None


class DeviceCode(ValueObject):
    """Show `verification_uri_complete` and `user_code` to a person; the app polls by itself."""

    user_code: str
    verification_uri: str
    verification_uri_complete: str = ''
    expires_in: int = 600
    interval: int = 5
