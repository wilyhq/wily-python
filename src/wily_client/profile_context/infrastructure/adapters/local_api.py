from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from wily_client.common.infrastructure.local_api import LONG_TIMEOUT
from wily_client.profile_context.domains.entities.profile import Folder, Profile
from wily_client.profile_context.domains.value_objects.profile import Launch

if TYPE_CHECKING:
    import builtins

    from wily_client.common.infrastructure.local_api import LocalApi
    from wily_client.profile_context.domains.dto.profile import ProfileChanges, ProfileDraft, ProfileFilter


def _path(profile_id: str, tail: str = '') -> str:
    return f'/v1/profiles/{quote(profile_id, safe="")}{tail}'


def _profile(answer: dict[str, Any]) -> Profile:
    return Profile.model_validate({**answer['profile'], 'etag': answer.get('etag')})


class ProfileLocalApiAdapter:
    def __init__(self, api: LocalApi) -> None:
        self._api = api

    def list(self, profile_filter: ProfileFilter) -> builtins.list[Profile]:
        answer = self._api.call('GET', '/v1/profiles', params=profile_filter.to_body())
        return [Profile.model_validate(p) for p in answer.get('profiles', [])]

    def get(self, profile_id: str) -> Profile:
        return _profile(self._api.call('GET', _path(profile_id)))

    def create(self, draft: ProfileDraft) -> Profile:
        return _profile(self._api.call('POST', '/v1/profiles', json=draft.to_body()))

    def update(self, profile_id: str, changes: ProfileChanges, if_match: str | None) -> Profile:
        headers = {'If-Match': if_match} if if_match else None
        return _profile(self._api.call('PATCH', _path(profile_id), json=changes.to_body(), headers=headers))

    def delete(self, profile_id: str) -> None:
        self._api.call('DELETE', _path(profile_id))

    def restore(self, profile_id: str) -> Profile:
        return _profile(self._api.call('POST', _path(profile_id, '/restore')))

    def clone(self, profile_id: str) -> Profile:
        return _profile(self._api.call('POST', _path(profile_id, '/clone')))

    def launch(self, profile_id: str) -> Launch:
        d = self._api.call('POST', _path(profile_id, '/launch'), timeout=LONG_TIMEOUT)
        return Launch.model_validate({**d, **(d.get('launched') or {})})

    def folders(self) -> builtins.list[Folder]:
        return [Folder.model_validate(f) for f in self._api.call('GET', '/v1/profile-folders').get('folders', [])]

    def create_folder(self, name: str) -> Folder:
        return Folder.model_validate(self._api.call('POST', '/v1/profile-folders', json={'name': name})['folder'])

    def delete_folder(self, folder_id: str) -> None:
        self._api.call('DELETE', f'/v1/profile-folders/{quote(folder_id, safe="")}')
