"""Reads `desktop.json`. No file means no app is running (the app removes it on a clean exit)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import ValidationError

from wily_client.common.domains.door import Discovery
from wily_client.common.domains.errors import UnavailableError

if TYPE_CHECKING:
    from pathlib import Path

NOT_RUNNING = 'the wily app is not running: start it, or run `wily serve` (no discovery file at {path})'


def read_discovery(path: Path) -> Discovery:
    try:
        text = path.read_text(encoding='utf-8')
    except FileNotFoundError:
        raise UnavailableError(NOT_RUNNING.format(path=path)) from None
    except OSError as e:
        raise UnavailableError(f'cannot read {path}: {e}') from e
    try:
        return Discovery.model_validate_json(text)
    except ValidationError as e:
        raise UnavailableError(f'{path} is not a discovery file: {e.error_count()} bad field(s)') from e
