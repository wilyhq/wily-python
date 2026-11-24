from __future__ import annotations

from enum import StrEnum

# Switches the app sets itself or that open the browser to others (the app refuses them too).
FORBIDDEN_ARGS = (
    '--remote-debugging-',
    '--remote-allow-origins',
    '--user-data-dir',
    '--profile-directory',
    '--load-extension',
    '--disable-extensions-except',
    '--disable-web-security',
    '--proxy-',
    '--no-proxy-server',
    '--host-resolver-rules',
    '--host-rules',
    '--no-sandbox',
    '--enable-automation',
    '--headless',
    '--user-agent',
    '--lang',
    '--accept-lang',
    '--force-webrtc-ip-handling-policy',
    '--webrtc-ip-handling-policy',
    '--disable-site-isolation-trials',
    '--ignore-certificate-errors',
)
ARGS_MAX = 50
ARG_MAX = 200
BOOKMARKS_MAX = 500


class ProfileOs(StrEnum):
    MACOS = 'macos'
    WINDOWS11 = 'windows11'
    WINDOWS10 = 'windows10'
    LINUX = 'linux'


class WebrtcMode(StrEnum):
    """`proxy` — WebRTC shows the proxy's exit; `off` — no WebRTC; `real` — the machine's own address."""

    PROXY = 'proxy'
    OFF = 'off'
    REAL = 'real'


class ProfileState(StrEnum):
    RUNNING = 'running'
    STOPPED = 'stopped'
