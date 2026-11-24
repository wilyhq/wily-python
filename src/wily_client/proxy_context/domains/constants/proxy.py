from __future__ import annotations

from enum import StrEnum


class ProxyProtocol(StrEnum):
    HTTP = 'http'
    HTTPS = 'https'
    SOCKS5 = 'socks5'


class ProxyKind(StrEnum):
    RESIDENTIAL = 'residential'
    MOBILE = 'mobile'
    DATACENTER = 'datacenter'
    ISP = 'isp'
    UNKNOWN = 'unknown'
