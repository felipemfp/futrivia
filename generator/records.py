"""Source-independent records. Every adapter produces these; templates read only these."""
from dataclasses import dataclass

# (club key, season) — formatted for players only when the day file is written.
Evidence = tuple[str, int]


@dataclass(frozen=True)
class Match:
    match_id: str
    season: int
    date: str
    home: str
    away: str
    home_goals: int
    away_goals: int


@dataclass(frozen=True)
class Goal:
    match_id: str
    season: int
    date: str
    club: str
    player: str
    player_ref: str
    minute: str
    penalty: bool
    own_goal: bool


@dataclass(frozen=True)
class Card:
    match_id: str
    season: int
    date: str
    club: str
    player: str
    player_ref: str
    red: bool


@dataclass(frozen=True)
class LineupEntry:
    match_id: str
    season: int
    date: str
    club: str
    player: str
    player_ref: str
    position: str
    starter: bool


@dataclass(frozen=True)
class PromptCandidate:
    id: str
    template: str
    text: str
    # player_ref -> evidence, one entry per qualifying occurrence
    answers: dict[str, tuple[Evidence, ...]]
