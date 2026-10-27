"""Read-only projection of the consolidated platform, separate from operational actions."""

from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict


class Projection(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class MapTotals(Projection):
    action_count: int
    participation_count: int
    people_count: int


class MapSummary(MapTotals):
    municipality_count: int
    undated_action_count: int
    unallocated: MapTotals


class MapMunicipality(Projection):
    code: str
    name: str
    action_count: int
    unallocated_action_count: int
    single_municipality_participations: int
    single_municipality_people: int


class PublishedMap(Projection):
    status: Literal[
        "available",
        "empty",
        "unavailable",
        "not_configured",
        "unauthorized",
        "contract_unavailable",
    ]
    checked_at: str
    refresh_after_seconds: int
    generation: str | None
    captured_at: str | None
    expires_at: str | None
    summary: MapSummary | None
    municipalities: list[MapMunicipality]


class PublishedMapSource(Protocol):
    async def read(self) -> PublishedMap: ...
