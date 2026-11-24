from __future__ import annotations

from datetime import datetime

from wily_client.common.domains.model import ValueObject


class ProxyCheck(ValueObject):
    """One check of a proxy by the server: where it exits and how fast."""

    status: str
    exit_ip: str | None = None
    exit_country: str | None = None
    latency_ms: int | None = None
    error_code: str | None = None
    checked_at: datetime | None = None

    @property
    def ok(self) -> bool:
        return self.status == 'ok'
