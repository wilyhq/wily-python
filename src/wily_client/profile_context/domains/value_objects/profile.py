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
    proxy_server: str | None = None
    """What this browser goes through: the proxy, or the app's local forwarder `http://127.0.0.1:<port>`."""
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


class ProfileProxy(ValueObject):
    """A profile's proxy as the app connects to it — two ways for a script to leave through the profile's exit.

    `proxy_server` is what the profile's running browser goes through: for a proxy with a login, the app's local
    forwarder `http://127.0.0.1:<port>`, usable from this machine without the password; `None` while the profile
    does not run in this app. `upstream` is the provider's address with the login and password this profile gets,
    `{session}` already filled by the server — the same sticky session as the browser, so the same exit, with or
    without the browser running. It carries the password: hidden from `repr`, do not log it.
    """

    profile_id: str
    running: bool
    proxy_id: str
    name: str
    proxy_server: str | None = None
    upstream: str = Field(repr=False)


class RunningBrowser(ValueObject):
    """A profile's browser running on this machine — whoever started it: a script or the app's window."""

    profile_id: str
    pid: int | None
    user_data_dir: Path
    devtools: DevTools
    proxy_server: str | None = None
    """What the browser goes through: `scheme://host:port` of the proxy, or the app's local forwarder
    `http://127.0.0.1:<port>` for a proxy with a login — reachable from this machine without the password."""
