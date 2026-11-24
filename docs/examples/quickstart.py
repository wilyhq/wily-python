"""Is the app running, and who is signed in? `python docs/examples/quickstart.py`"""

from wily_client import AuthRequiredError, UnavailableError, Wily


def main() -> None:
    try:
        wily = Wily.connect()
    except UnavailableError as e:
        print(e)  # the app is not running: start it, or `wily serve`
        return
    with wily:
        health = wily.app.health()
        print(f'{health.app} {health.version} (pid {health.pid}) via {wily.door.kind.value}')
        try:
            print('signed in as', wily.app.whoami().email)
        except AuthRequiredError:
            print('not signed in: run `wily login` or docs/examples/sign_in.py')


if __name__ == '__main__':
    main()
