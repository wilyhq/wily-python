"""The one HTTP client of the library: httpx over the app's door, errors turned into `WilyError`.

Every adapter of every context talks to the app through `LocalApi.call`; none of them knows which door
it went through. Answers are the CLI's JSON (`wily … --json`), an object per operation.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import httpx

from wily_client.common.domains.door import Door, DoorKind
from wily_client.common.domains.errors import UnavailableError, WilyError, error_for

if TYPE_CHECKING:
    from collections.abc import Mapping
    from types import TracebackType

log = logging.getLogger('wily_client')

DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=5.0)
# Starting a browser or installing a core can take minutes; the app holds the request open meanwhile.
LONG_TIMEOUT = httpx.Timeout(600.0, connect=5.0)


def transport_for(door: Door) -> httpx.BaseTransport:
    if door.kind is DoorKind.UNIX_SOCKET:
        return httpx.HTTPTransport(uds=door.address)
    if door.kind is DoorKind.NAMED_PIPE:
        from wily_client.common.infrastructure.pipe import NamedPipeTransport  # noqa: PLC0415

        return NamedPipeTransport(door.address)
    return httpx.HTTPTransport()


class LocalApi:
    def __init__(
        self, door: Door, *, timeout: httpx.Timeout = DEFAULT_TIMEOUT, transport: httpx.BaseTransport | None = None
    ) -> None:
        headers = {'User-Agent': 'wily-client-python'}
        if door.token:
            headers['Authorization'] = f'Bearer {door.token}'
        self.door = door
        self._http = httpx.Client(
            base_url=door.base_url,
            transport=transport or transport_for(door),
            headers=headers,
            timeout=timeout,
        )

    def call(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: httpx.Timeout | None = None,
    ) -> dict[str, Any]:
        """The answer's JSON object; any error answer raises the `WilyError` for its code."""
        response = self.send(method, path, json=json, params=params, headers=headers, timeout=timeout)
        return _body(response)

    def send(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: httpx.Timeout | None = None,
    ) -> httpx.Response:
        clean = {k: _param(v) for k, v in (params or {}).items() if v is not None}
        try:
            response = self._http.request(
                method,
                path,
                json=json,
                params=clean,
                headers=dict(headers or {}),
                timeout=timeout or self._http.timeout,
            )
        except httpx.TimeoutException as e:
            raise UnavailableError(f'the wily app did not answer {method} {path} in time: {e}') from e
        except httpx.TransportError as e:
            raise UnavailableError(f'cannot reach the wily app at {self.door.address}: {e}') from e
        log.debug('%s %s -> %s', method, path, response.status_code)
        if response.is_error:
            raise _error(response)
        return response

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> LocalApi:
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None) -> None:
        self.close()


def _param(value: Any) -> Any:
    return ('true' if value else 'false') if isinstance(value, bool) else value


def _body(response: httpx.Response) -> dict[str, Any]:
    if not response.content:
        return {}
    data = response.json()
    if not isinstance(data, dict):
        raise WilyError(f'expected a JSON object, got {type(data).__name__}', status=response.status_code)
    return data


def _error(response: httpx.Response) -> WilyError:
    try:
        err = response.json().get('error') or {}
    except (ValueError, AttributeError):
        err = {}
    if response.status_code == httpx.codes.UNAUTHORIZED and not err:
        return error_for('auth_required', 'the app refused the token: re-read desktop.json', status=401)
    if response.status_code == httpx.codes.FORBIDDEN and not err:
        return error_for('denied', 'the app refused this request (browser-like or foreign Host)', status=403)
    if response.status_code == httpx.codes.NOT_FOUND and not err:
        return error_for('not_found', f'the app has no {response.request.url.path}', status=404)
    message = err.get('message') or response.text or response.reason_phrase
    return error_for(str(err.get('code', 'failure')), message, status=response.status_code)
