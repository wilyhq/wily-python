"""Errors of the local API, one class per `error.code`.

The desktop app answers an error as `{"error": {"code", "exit_code", "message"}}` — the same contract as
`wily … --json` (https://wily.bot/docs/agents/). The code says what to do; the class lets a
script catch exactly the case it can handle.
"""

from __future__ import annotations

from typing import ClassVar


class WilyError(Exception):
    """Any error the local API returned, or a failure to reach it."""

    code: ClassVar[str] = 'failure'
    exit_code: ClassVar[int] = 1

    def __init__(self, message: str, *, status: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status = status

    def __str__(self) -> str:
        return f'{self.code}: {self.message}'


class UsageError(WilyError):
    """The arguments are wrong: fix the call."""

    code = 'usage'
    exit_code = 2


class AuthRequiredError(WilyError):
    """This machine is not signed in: `wily login`, or `Wily.app.login_device()`."""

    code = 'auth_required'
    exit_code = 3


class NetworkError(WilyError):
    """The wily server (api.wily.bot) is unreachable from the app; try later."""

    code = 'network'
    exit_code = 4


class NotFoundError(WilyError):
    """No such object."""

    code = 'not_found'
    exit_code = 5


class ConflictError(WilyError):
    """The object is not in a state for this: already running, in the trash, changed elsewhere."""

    code = 'conflict'
    exit_code = 6


class DeniedError(WilyError):
    """Sign-in was refused, cancelled or expired."""

    code = 'denied'
    exit_code = 7


class UnsupportedError(WilyError):
    """The server or the app lacks the feature: update the app."""

    code = 'unsupported'
    exit_code = 8


class UnavailableError(WilyError):
    """The desktop app does not answer: start it, or run `wily serve`."""

    code = 'unavailable'
    exit_code = 9


class LeaseRequiredError(WilyError):
    """The device's access lease is missing or expired: go online, or sign in with a device code."""

    code = 'lease_required'
    exit_code = 10


ERRORS: dict[str, type[WilyError]] = {
    cls.code: cls
    for cls in (
        WilyError,
        UsageError,
        AuthRequiredError,
        NetworkError,
        NotFoundError,
        ConflictError,
        DeniedError,
        UnsupportedError,
        UnavailableError,
        LeaseRequiredError,
    )
}


def error_for(code: str, message: str, *, status: int | None = None) -> WilyError:
    """The error class for `code`; an unknown code is a plain `WilyError` carrying the message."""
    return ERRORS.get(code, WilyError)(message, status=status)
