# Architecture

The library follows the same Domain-Driven Design layering as our Python services, read as **hexagonal architecture**: the domain and the applications in
the middle, the app's HTTP API as one adapter at the edge, the Python API as the port a script drives.

## Contexts

| package | ubiquitous language | public as |
|---|---|---|
| `wily_client.app_context` | the app itself, health, sign-in on this machine | `wily.app` |
| `wily_client.proxy_context` | proxies, their checks, imports | `wily.proxies` |
| `wily_client.profile_context` | profiles, folders, launches, DevTools endpoints | `wily.profiles` |
| `wily_client.common` | the shared kernel: errors, doors, the HTTP client to the app | — |

Contexts never import each other (`import-linter`: *Context independence*). What two of them share lives in
`common`.

## Layers

Inside each context, from the edge inward — the same names as in our services:

```text
<context>/
├── infrastructure/
│   └── adapters/        # driven adapters: local_api.py (httpx → the app), devtools_file.py (a file Chromium writes)
├── applications/        # what a script calls: ProxyApplication, ProfileApplication, AppApplication
│   └── gateway.py       # the ports applications need, as typing.Protocol — implemented by adapters
├── services/            # pure logic that belongs to no single model (common/services/choose_door.py)
└── domains/
    ├── constants/       # enums: ProxyProtocol, ProfileOs, WebrtcMode, forbidden launch switches
    ├── entities/        # Proxy, Profile, Folder — equal by id
    ├── value_objects/   # ProxyCheck, Launch, DevTools, Health — equal by value
    └── dto/             # ProxyDraft, ProfileChanges, ProfileFilter — what a script sends, validated
```

The composition root `wily_client/client.py` (`Wily`) is the only place that builds adapters and hands them to
applications. Swap an adapter — a fake in a test, another transport — and nothing inside changes.

Who may import whom, checked by `make imports` (`lint-imports.toml`):

| contract | rule |
|---|---|
| Layers | `infrastructure` → `applications` → `services` → `domains`, never upward |
| Domain purity | no `httpx`/`httpcore` in any `domains` |
| Applications see ports | no `httpx`, `httpcore` or `infrastructure` in any `applications` |
| Composition root | `client` → contexts → `common` |
| Context independence | `app_context`, `proxy_context`, `profile_context` do not import each other |

## Models: pydantic

Entities, value objects and DTOs are pydantic v2 models (`common/domains/model.py`), the way `dddesign` builds them in
our services; `dddesign` itself is not a dependency because it caps Python below 3.14.

- **Entities and value objects** are frozen and ignore unknown fields: the app grows faster than the library, and a
  new field must not break an old script.
- **DTOs** forbid unknown fields and carry every rule on a value (ranges, patterns, enums, custom validators), so a
  bad call fails in the script with the field named — before any request is made. `to_body()` sends only the
  fields that were set, which is what makes `update(id, notes='x')` a partial change.
- **Rich models**: behaviour sits on the model that owns the data — `Proxy.url()`, `Proxy.alive`, `Profile.running`,
  `DevTools.http_url`.

## Transport

`common/infrastructure/local_api.py` is the only HTTP client: one `httpx.Client` per `Wily`, its transport chosen by
the door (`common/services/choose_door.py`): `uds=` for a Unix socket, `NamedPipeTransport`
(`common/infrastructure/pipe.py`) for a Windows pipe, plain TCP with a Bearer token for the debug door. Error answers
become `WilyError` subclasses there, so no adapter parses errors itself.
