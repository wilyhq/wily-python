# Errors

Every error the app returns is `{"error": {"code", "exit_code", "message"}}` — the same contract as
`wily … --json` — and the library raises the class for its code. All of them derive from `WilyError`, which has
`code`, `exit_code`, `message` and the HTTP `status`.

| class | code | exit | what to do |
|---|---|---|---|
| `UsageError` | `usage` | 2 | fix the call |
| `AuthRequiredError` | `auth_required` | 3 | sign in: `wily login`, or `wily.app.login_device()` |
| `NetworkError` | `network` | 4 | the app cannot reach api.wily.bot; try later |
| `NotFoundError` | `not_found` | 5 | no such object (or an older app without this route) |
| `ConflictError` | `conflict` | 6 | wrong state: already running, in the trash, changed elsewhere, no core installed |
| `DeniedError` | `denied` | 7 | sign-in refused, cancelled or expired: start again; do not retry in a loop |
| `UnsupportedError` | `unsupported` | 8 | the app or server lacks the feature: update the app |
| `UnavailableError` | `unavailable` | 9 | the app is not running or does not answer: start it, or `wily serve` |
| `LeaseRequiredError` | `lease_required` | 10 | the device's access lease expired: go online, or sign in with a device code |
| `WilyError` | `failure` | 1 | anything else; read `message` |

Values a script passes are checked before sending, so a wrong port or protocol raises
`pydantic.ValidationError`, not one of the above.

```python
from wily_client import AuthRequiredError, UnavailableError, Wily

try:
    with Wily.connect() as wily:
        proxies = wily.proxies.list()
except UnavailableError:
    print('start the wily app first')
except AuthRequiredError:
    print('sign in first: wily login')
```
