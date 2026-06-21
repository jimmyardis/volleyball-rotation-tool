"""Pydantic request/response models for the API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TeamCreate(BaseModel):
    name: str
    season: str | None = None


class PlayerAttrs(BaseModel):
    setting: int | None = None
    defense: int | None = None
    attacking: int | None = None
    blocking: int | None = None
    confidence: int | None = None
    pressure: int | None = None


class PlayerCreate(PlayerAttrs):
    name: str
    primary_role: str = Field(..., description="S, OH, MB, OPP, L, DS")
    jersey_number: int | None = None
    secondary_role: str | None = None
    is_libero: bool = False
    dominant_hand: str | None = None  # 'L' / 'R' / None — unused in P1


class PlayerUpdate(PlayerAttrs):
    name: str | None = None
    primary_role: str | None = None
    jersey_number: int | None = None
    secondary_role: str | None = None
    is_libero: bool | None = None
    dominant_hand: str | None = None


class LineupCreate(BaseModel):
    name: str
    system: str = "5-1"
    notes: str | None = None


class LineupPositions(BaseModel):
    # zone (1..6, as string keys over JSON) -> player_id
    positions: dict[int, int]


class OverlapCheck(BaseModel):
    # zone -> [x, y]
    coords: dict[int, tuple[float, float]]


class FormationSave(BaseModel):
    # player_id -> [x, y], normalized (x left->right, y net->baseline)
    placements: dict[int, tuple[float, float]]


class SubsSave(BaseModel):
    # starter_id -> on_court_id (who actually plays that slot this rotation)
    swaps: dict[int, int]


class CoverageSave(BaseModel):
    # player_id -> 'all' | 'front' | 'back'
    coverage: dict[int, str]


class PairsSave(BaseModel):
    # [[front_player_id, back_player_id], ...]
    pairs: list[tuple[int, int]]


class ChatTurn(BaseModel):
    role: str          # 'user' | 'assistant'
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatTurn]
    team_id: int | None = None      # optional: gives the assistant the roster
    lineup_id: int | None = None    # optional: gives it the lineup's rotations


class SimRequest(BaseModel):
    stakes: float = 0.5            # 0..1 (low / medium / high game)
    opponent_skill: int = 60       # 1..100
    games: int = 10000
