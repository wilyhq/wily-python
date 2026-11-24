from __future__ import annotations

from datetime import datetime

from pydantic import Field

from wily_client.common.domains.model import Entity
from wily_client.profile_context.domains.constants.profile import ProfileState
from wily_client.profile_context.domains.value_objects.profile import Bookmark, FolderRef, ProxyRef


class Profile(Entity):
    """A browser profile (`ProfileOut` of https://api.wily.bot/api/openapi.json). `etag` is set by `get` and guards `update`."""

    name: str
    folder: FolderRef | None = None
    tags: list[str] = Field(default_factory=list)
    notes: str = ''
    os: str = ''
    core: str = ''
    proxy: ProxyRef | None = None
    geo_from_proxy: bool = True
    timezone: str | None = None
    locale: str | None = None
    webrtc: str = 'proxy'
    start_url: str | None = None
    bookmarks: list[Bookmark] = Field(default_factory=list)
    launch_args: list[str] = Field(default_factory=list)
    state: str = ProfileState.STOPPED.value
    pinned: bool = False
    version: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
    etag: str | None = Field(default=None, repr=False)

    @property
    def running(self) -> bool:
        return self.state == ProfileState.RUNNING.value

    @property
    def trashed(self) -> bool:
        return self.deleted_at is not None


class Folder(Entity):
    name: str
