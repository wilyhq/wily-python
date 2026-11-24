# Proxies — `wily.proxies`

Proxies belong to the account's workspace: the app keeps them on api.wily.bot, so a proxy made here shows in the app,
in the web console and on every device signed in to the same account.

| call | does |
|---|---|
| `list()` | every proxy of the workspace → `list[Proxy]` |
| `get(id)` / `find(name)` | one proxy, by id or by its exact name |
| `create(draft)` / `create(**fields)` | a new proxy → `Proxy` |
| `update(id, **fields)` | change only the fields given → `Proxy` |
| `delete(id)` | delete it |
| `check(id)` | check a saved proxy from the server → `ProxyCheck` (exit IP, country, latency) |
| `check_draft(draft)` | the same before saving |
| `import_text(text, dry_run=True)` | a pasted list, one per line; dry run by default |

```python
from wily_client import ProxyDraft, ProxyProtocol, Wily

with Wily.connect() as wily:
    proxy = wily.proxies.create(ProxyDraft(
        name='de-1', protocol=ProxyProtocol.SOCKS5, host='gate.example.net', port=1080,
        username='customer-{session}', password='secret', country='de',
    ))
    check = wily.proxies.check(proxy.id)
    print(check.ok, check.exit_ip, check.exit_country)
```

## Validation

`ProxyDraft` and `ProxyChanges` are pydantic models, and `create(**fields)` builds one. Everything is checked
before the call leaves the script, and a bad value raises `pydantic.ValidationError` naming the field:

| field | rule |
|---|---|
| `name` | 1–200 characters, trimmed |
| `protocol` | `http`, `https`, `socks5` |
| `host` | no spaces, `/`, `:` or `@` |
| `port` | 1–65535 |
| `country` | two letters, upper-cased for you (`de` → `DE`) |
| `kind` | `residential`, `mobile`, `datacenter`, `isp`, `unknown` |
| `rotate_url` | an http(s) URL |
| anything else | refused: a typo in a field name is an error, not a silently ignored key |

`update` sends only the fields you pass: `update(id, notes='x')` changes the notes and nothing else.

## The `Proxy` object

`id`, `name`, `protocol`, `host`, `port`, `username`, `password`, `kind`, `country`, `notes`, `last_check`,
`profiles_count`, `created_at`, `updated_at`, and:

- `alive` — the last check's verdict, `None` if it was never checked;
- `url()` — `socks5://user:pass@host:port` with the login escaped, for httpx, requests or Playwright;
  `url(with_credentials=False)` for a log line.

`password` is plaintext, as the account stores it (vendors put the country and the session in it). It is hidden from
`repr(proxy)`; do not log `proxy.model_dump()` whole.

Fields the app adds later are ignored rather than refused, so a newer app does not break an older script.
