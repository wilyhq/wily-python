"""wily-client — drive the wily desktop app from Python: proxies, profiles, launching browsers.

Talks to the app's local API over its Unix socket (macOS, Linux) or named pipe (Windows).
"""

from wily_client.app_context.domains.value_objects.app import AuthStatus, DeviceCode, Health, User
from wily_client.client import Wily
from wily_client.common.domains.door import Door, DoorKind
from wily_client.common.domains.errors import (
    AuthRequiredError,
    ConflictError,
    DeniedError,
    LeaseRequiredError,
    NetworkError,
    NotFoundError,
    UnavailableError,
    UnsupportedError,
    UsageError,
    WilyError,
)
from wily_client.profile_context.domains.constants.profile import ProfileOs, WebrtcMode
from wily_client.profile_context.domains.dto.profile import ProfileChanges, ProfileDraft, ProfileFilter
from wily_client.profile_context.domains.entities.profile import Folder, Profile
from wily_client.profile_context.domains.value_objects.profile import Bookmark, DevTools, Launch, ProfileProxy, RunningBrowser
from wily_client.proxy_context.domains.constants.proxy import ProxyKind, ProxyProtocol
from wily_client.proxy_context.domains.dto.proxy import ProxyChanges, ProxyDraft
from wily_client.proxy_context.domains.entities.proxy import Proxy
from wily_client.proxy_context.domains.value_objects.proxy_check import ProxyCheck

__version__ = '0.1.0'

__all__ = [
    'AuthRequiredError',
    'AuthStatus',
    'Bookmark',
    'ConflictError',
    'DeniedError',
    'DevTools',
    'DeviceCode',
    'Door',
    'DoorKind',
    'Folder',
    'Health',
    'Launch',
    'LeaseRequiredError',
    'NetworkError',
    'NotFoundError',
    'Profile',
    'ProfileChanges',
    'ProfileDraft',
    'ProfileFilter',
    'ProfileOs',
    'Proxy',
    'ProxyChanges',
    'ProxyCheck',
    'ProxyDraft',
    'ProxyKind',
    'ProxyProtocol',
    'ProfileProxy',
    'RunningBrowser',
    'UnavailableError',
    'UnsupportedError',
    'UsageError',
    'User',
    'WebrtcMode',
    'Wily',
    'WilyError',
    '__version__',
]
