"""What a script sends about profiles. Pydantic checks every value before the call goes out.

The launch-argument rules repeat the app's own so a bad switch fails in the script, with
the field named, instead of a round trip later; the app still checks them itself.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator, Field, HttpUrl, StringConstraints, field_validator

from wily_client.common.domains.model import DataTransferObject
from wily_client.profile_context.domains.constants.profile import (
    ARG_MAX,
    ARGS_MAX,
    BOOKMARKS_MAX,
    FORBIDDEN_ARGS,
    ProfileOs,
    WebrtcMode,
)
from wily_client.profile_context.domains.value_objects.profile import Bookmark


def _switch(arg: str) -> str:
    name = arg.split('=', 1)[0].lower()
    prefixes = tuple(f for f in FORBIDDEN_ARGS if f.endswith('-'))
    if name in FORBIDDEN_ARGS or name.startswith(prefixes):
        raise ValueError(f'`{arg}` is set by wily itself or opens the browser to others')
    return arg


Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Tag = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
Uuid = Annotated[str, StringConstraints(pattern=r'^[0-9a-fA-F-]{36}$')]
Switch = Annotated[
    str,
    StringConstraints(max_length=ARG_MAX, pattern=r'^--[A-Za-z0-9][A-Za-z0-9-]*(=.*)?$'),
    AfterValidator(_switch),
]
Switches = Annotated[list[Switch], Field(max_length=ARGS_MAX)]
Bookmarks = Annotated[list[Bookmark], Field(max_length=BOOKMARKS_MAX)]
Timezone = Annotated[str, StringConstraints(pattern=r'^[A-Za-z_]+(/[A-Za-z0-9_+-]+)*$')]
Locale = Annotated[str, StringConstraints(pattern=r'^[a-z]{2,3}(-[A-Za-z0-9]{2,8})*$')]


class _ProfileFields(DataTransferObject):
    folder_id: Uuid | None = None
    tags: list[Tag] | None = None
    notes: str | None = None
    os: ProfileOs | None = None
    core: str | None = None
    proxy_id: Uuid | None = None
    geo_from_proxy: bool | None = None
    timezone: Timezone | None = None
    locale: Locale | None = None
    webrtc: WebrtcMode | None = None
    start_url: HttpUrl | None = None
    bookmarks: Bookmarks | None = None
    launch_args: Switches | None = None

    @field_validator('start_url')
    @classmethod
    def _web_only(cls, v: HttpUrl | None) -> HttpUrl | None:
        if v is not None and v.scheme not in {'http', 'https'}:
            raise ValueError('only http:// and https:// addresses')
        return v


class ProfileDraft(_ProfileFields):
    """A new profile. Everything is optional: the workspace's defaults fill the rest."""

    name: Name | None = None


class ProfileChanges(_ProfileFields):
    """A change: only the fields set here are sent."""

    name: Name | None = None
    pinned: bool | None = None


class ProfileFilter(DataTransferObject):
    q: str | None = None
    folder_id: Uuid | None = None
    tag: Tag | None = None
    proxy_id: Uuid | None = None
    trash: bool | None = None
