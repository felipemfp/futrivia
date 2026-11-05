"""Adapter for dcaribou/transfermarkt-datasets: Série A 2025 and 2026 to 1 June, with lineups, goals and cards.

Transfermarkt labels a season with the year before: its "2024" season is Brasileirão 2025.
A goal event's club is the club credited with the goal, so own goals sit under the beneficiary.
"""
import csv
import gzip
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from generator import clubs
from generator.records import Card, Goal, LineupEntry, Match

SOURCE = "transfermarkt"
COMPETITION = "BRA1"


@dataclass(frozen=True)
class Data:
    matches: dict[str, Match]
    goals: list[Goal]
    cards: list[Card]
    lineups: list[LineupEntry]
    names: dict[str, str]  # player_ref -> name


def _ref(player_id: str) -> str:
    return f"{SOURCE}:{player_id}"


def build(games: Iterable[dict], events: Iterable[dict], lineups: Iterable[dict], players: Iterable[dict]) -> Data:
    matches = {}
    for g in games:
        if g["competition_id"] != COMPETITION:
            continue
        matches[f"tm:{g['game_id']}"] = Match(
            match_id=f"tm:{g['game_id']}",
            season=int(g["season"]) + 1,
            date=g["date"],
            home=clubs.TRANSFERMARKT[g["home_club_id"]],
            away=clubs.TRANSFERMARKT[g["away_club_id"]],
            home_goals=int(g["home_club_goals"]),
            away_goals=int(g["away_club_goals"]),
        )

    lineup_rows = [row for row in lineups if f"tm:{row['game_id']}" in matches]
    # players.csv lacks some players; their lineup rows still carry a name.
    names = {_ref(row["player_id"]): row["player_name"] for row in lineup_rows}
    names.update({_ref(p["player_id"]): p["name"] for p in players})

    goals, cards = [], []
    for e in events:
        match = matches.get(f"tm:{e['game_id']}")
        if match is None or e["type"] not in ("Goals", "Cards"):
            continue
        ref = _ref(e["player_id"])
        common = dict(match_id=match.match_id, season=match.season, date=match.date,
                      club=clubs.TRANSFERMARKT[e["club_id"]], player=names[ref], player_ref=ref)
        if e["type"] == "Goals":
            description = e["description"]
            goals.append(Goal(**common, minute=e.get("minute", ""), penalty=", Penalty" in description,
                              own_goal="Own-goal" in description))
        else:
            description = e["description"]
            cards.append(Card(**common, red="Red card" in description or "Second yellow" in description))

    entries = []
    for row in lineup_rows:
        match = matches[f"tm:{row['game_id']}"]
        ref = _ref(row["player_id"])
        entries.append(LineupEntry(match_id=match.match_id, season=match.season, date=match.date,
                                   club=clubs.TRANSFERMARKT[row["club_id"]], player=names[ref],
                                   player_ref=ref, position=row["position"], starter=row["type"] == "starting_lineup"))
    return Data(matches, goals, cards, entries, names)


def _rows(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        yield from csv.DictReader(handle)


def load(cache: Path) -> Data:
    return build(_rows(cache / "games.csv.gz"), _rows(cache / "game_events.csv.gz"),
                 _rows(cache / "game_lineups.csv.gz"), _rows(cache / "players.csv.gz"))
