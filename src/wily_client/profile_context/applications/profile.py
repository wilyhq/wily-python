from __future__ import annotations

import time
from contextlib import contextmanager, suppress
from typing import TYPE_CHECKING, Any

from wily_client.common.domains.errors import NotFoundError, UnavailableError
from wily_client.profile_context.domains.dto.profile import ProfileChanges, ProfileDraft, ProfileFilter

if TYPE_CHECKING:
    import builtins
    from collections.abc import Iterator

    from wily_client.profile_context.applications.gateway import BrowserGateway, DevToolsGateway, ProfileGateway
    from wily_client.profile_context.domains.entities.profile import Folder, Profile
    from wily_client.profile_context.domains.value_objects.profile import DevTools, Launch


class ProfileApplication:
    """`wily.profiles`: browser profiles — list, create, change, trash, and launch on this machine."""

    def __init__(self, gateway: ProfileGateway, devtools: DevToolsGateway, browser: BrowserGateway) -> None:
        self._gateway = gateway
        self._devtools = devtools
        self._browser = browser

    def list(self, profile_filter: ProfileFilter | None = None, **fields: Any) -> builtins.list[Profile]:
        return self._gateway.list(profile_filter or ProfileFilter(**fields))

    def get(self, profile_id: str) -> Profile:
        return self._gateway.get(profile_id)

    def find(self, name: str) -> Profile:
        """The one profile with this exact name (outside the trash)."""
        found = [p for p in self._gateway.list(ProfileFilter(q=name)) if p.name == name]
        if len(found) != 1:
            raise NotFoundError(f'{len(found)} profiles are named {name!r}')
        return found[0]

    def create(self, draft: ProfileDraft | None = None, **fields: Any) -> Profile:
        return self._gateway.create(draft or ProfileDraft(**fields))

    def update(self, profile: Profile | str, changes: ProfileChanges | None = None, **fields: Any) -> Profile:
        """Pass the `Profile` from `get` to refuse a change made elsewhere since (`If-Match`), or just its id."""
        if isinstance(profile, str):
            profile_id, etag = profile, None
        else:
            profile_id, etag = profile.id, profile.etag
        return self._gateway.update(profile_id, changes or ProfileChanges(**fields), etag)

    def delete(self, profile_id: str) -> None:
        """Moves the profile to the trash; `restore` brings it back."""
        self._gateway.delete(profile_id)

    def restore(self, profile_id: str) -> Profile:
        return self._gateway.restore(profile_id)

    def clone(self, profile_id: str) -> Profile:
        return self._gateway.clone(profile_id)

    def launch(self, profile_id: str) -> Launch:
        """Starts the profile's browser here, through its proxy. Needs an installed core and a sign-in."""
        return self._gateway.launch(profile_id)

    def devtools(self, launch: Launch, timeout: float = 30.0, interval: float = 0.2) -> DevTools:
        """The CDP endpoint of a launched browser, once it has written it — for Playwright or Puppeteer."""
        deadline = time.monotonic() + timeout
        while (found := self._devtools.read(launch.user_data_dir)) is None:
            if time.monotonic() >= deadline:
                raise UnavailableError(f'the browser of {launch.profile_id} wrote no DevTools port in {timeout} s')
            time.sleep(interval)
        return found

    def stop(self, launch: Launch, timeout: float = 30.0, interval: float = 0.5) -> Profile:
        """Closes the profile's browser (CDP `Browser.close`) and waits until the app reports it stopped.

        The app has no stop route yet, so this is what a person closing the window does: Chromium writes
        its cookies, the app saves the profile's state and releases its session.
        """
        found = self._devtools.read(launch.user_data_dir)
        if found is not None:
            with suppress(OSError):  # already gone: then only the wait below matters
                self._browser.send(found, 'Browser.close')
        deadline = time.monotonic() + timeout
        while (profile := self._gateway.get(launch.profile_id)).running:
            if time.monotonic() >= deadline:
                raise UnavailableError(f'{launch.profile_id} still runs {timeout} s after Browser.close')
            time.sleep(interval)
        return profile

    @contextmanager
    def running(self, profile_id: str, timeout: float = 30.0) -> Iterator[DevTools]:
        """Launch, hand over the CDP endpoint, stop on the way out — even if the block raised.

        ```python
        with wily.profiles.running(profile.id) as devtools:
            browser = playwright.chromium.connect_over_cdp(devtools.http_url)
        ```
        """
        launch = self.launch(profile_id)
        try:
            yield self.devtools(launch, timeout=timeout)
        finally:
            self.stop(launch, timeout=timeout)

    def folders(self) -> builtins.list[Folder]:
        return self._gateway.folders()

    def create_folder(self, name: str) -> Folder:
        return self._gateway.create_folder(name)

    def delete_folder(self, folder_id: str) -> None:
        self._gateway.delete_folder(folder_id)
