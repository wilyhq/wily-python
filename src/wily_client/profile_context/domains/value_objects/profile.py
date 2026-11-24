from __future__ import annotations

from pathlib import Path

from pydantic import Field

from wily_client.common.domains.model import ValueObject


class Bookmark(ValueObject):
    url: str
    title: str = ''
    folder: str | None = None


class FolderRef(ValueObject):
    id: str
    name: str


class ProxyRef(ValueObject):
    id: str
    name: str
    protocol: str | None = None
    country: str | None = None


class Launch(ValueObject):
    """A browser the app started for a profile, on this machine."""

    profile_id: str
    core: str
    pid: int
    executable: Path
    user_data_dir: Path
    session_id: str | None = None
    warnings: list[str] = Field(default_factory=list)


class DevTools(ValueObject):
    """Where the started browser listens for the Chrome DevTools Protocol, on 127.0.0.1."""

    port: int
    browser_path: str

    @property
    def http_url(self) -> str:
        """For Playwright `connect_over_cdp` and Puppeteer `browserURL`."""
        return f'http://127.0.0.1:{self.port}'

    @property
    def ws_url(self) -> str:
        return f'ws://127.0.0.1:{self.port}{self.browser_path}'
