"""Shared strict scalar and record types; no profile import in generic execution."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Commit = Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
Name = Annotated[str, Field(min_length=1, max_length=255)]
Positive = Annotated[int, Field(gt=0)]
Host = Annotated[str, Field(pattern=r"^[a-z0-9]+(?:[.-][a-z0-9]+)*$", max_length=253)]


class StrictRecord(BaseModel):
    """Reject unknown fields and type coercion at each nested boundary."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class VersionedRecord(StrictRecord):
    """Require an explicit integer schema version; booleans are not versions."""

    schema_version: Literal[1]

    @field_validator("schema_version", mode="before")
    @classmethod
    def integer_schema(cls, value: object) -> object:
        """Reject bool/string versions, e.g. schema_version=True raises ValueError."""
        if type(value) is not int:
            raise ValueError("schema_version must be an integer")
        return value
