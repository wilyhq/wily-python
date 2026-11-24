"""Profiles: create with a proxy, find, change safely, clone, trash and restore."""

from wily_client import ConflictError, ProfileOs, WebrtcMode, Wily


def main() -> None:
    with Wily.connect() as wily:
        proxy = wily.proxies.find('de-residential-1')
        folder = wily.profiles.create_folder('Shops')
        profile = wily.profiles.create(
            name='shop-de-1',
            folder_id=folder.id,
            os=ProfileOs.WINDOWS11,
            proxy_id=proxy.id,
            webrtc=WebrtcMode.PROXY,
            tags=['shop', 'de'],
            start_url='https://wily.bot/',
            launch_args=['--start-maximized'],
        )

        # `get` returns the profile with its ETag; passing it back to `update` refuses to overwrite
        # a change made meanwhile on another device.
        current = wily.profiles.get(profile.id)
        try:
            wily.profiles.update(current, notes='warmed up')
        except ConflictError:
            print('changed elsewhere: read it again and retry')

        for p in wily.profiles.list(tag='shop'):
            print(p.name, p.state, p.proxy.name if p.proxy else '-')

        copy = wily.profiles.clone(profile.id)
        wily.profiles.delete(copy.id)  # to the trash
        wily.profiles.restore(copy.id)


if __name__ == '__main__':
    main()
