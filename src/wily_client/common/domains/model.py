"""Base classes of the domain: pydantic models, as `dddesign` builds them in our services.

`dddesign` itself is not a dependency: it caps Python below 3.14, and a public library cannot. The split is
the same — an entity has an identity, a value object is equal by value, a DTO carries a request.

Unknown fields from the app are ignored rather than refused: the app grows faster than this library, and
an extra field must not break a script that does not use it. The whole answer stays in `raw` where a
model keeps one.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ValueObject(BaseModel):
    model_config = ConfigDict(frozen=True, extra='ignore', populate_by_name=True)


class Entity(BaseModel):
    """Equal by `id`, not by the values of its fields."""

    model_config = ConfigDict(frozen=True, extra='ignore', populate_by_name=True)

    id: str

    def __eq__(self, other: object) -> bool:
        return isinstance(other, type(self)) and other.id == self.id

    def __hash__(self) -> int:
        return hash((type(self).__name__, self.id))


class DataTransferObject(BaseModel):
    """What a script sends: only the fields it set go out (`model_dump(exclude_unset=True)`)."""

    model_config = ConfigDict(frozen=True, extra='forbid')

    def to_body(self) -> dict:
        return self.model_dump(mode='json', exclude_unset=True)
