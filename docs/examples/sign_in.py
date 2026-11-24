"""Sign this machine in with a device code — the way for a headless box or an agent."""

from wily_client import Wily


def main() -> None:
    with Wily.connect() as wily:
        if wily.app.auth_status().signed_in:
            print('already signed in')
            return
        code = wily.app.login_device()
        print(f'Open {code.verification_uri_complete} and confirm the code {code.user_code}')
        wily.app.wait_signed_in(timeout=code.expires_in)
        print('signed in as', wily.app.whoami().email)


if __name__ == '__main__':
    main()
