"""Adapter for adaoduque/Brasileirao_Dataset: Série A 2003–2024 results, with scorers and cards from 2014."""
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from generator.records import Card, Goal, Match

SOURCE = "adaoduque"


@dataclass(frozen=True)
class Data:
    matches: dict[str, Match]
    goals: list[Goal]
    cards: list[Card]


def _season(month: int, year: int) -> int:
    # Seasons start in April or later; January–March matches finish the previous season (2020 ran into 2021).
    return year - 1 if month <= 3 else year


def read_matches(rows: TextIO) -> dict[str, Match]:
    matches = {}
    for row in csv.DictReader(rows):
        day, month, year = (int(part) for part in row["data"].split("/"))
        matches[row["ID"]] = Match(
            match_id=row["ID"],
            season=_season(month, year),
            date=f"{year:04d}-{month:02d}-{day:02d}",
            home=row["mandante"],
            away=row["visitante"],
            home_goals=int(row["mandante_Placar"]),
            away_goals=int(row["visitante_Placar"]),
        )
    return matches


def read_goals(rows: TextIO, matches: dict[str, Match]) -> list[Goal]:
    goals = []
    for row in csv.DictReader(rows):
        match = matches[row["partida_id"]]
        goals.append(Goal(
            match_id=match.match_id,
            season=match.season,
            date=match.date,
            club=row["clube"],
            player=row["atleta"],
            player_ref=f"{SOURCE}:{row['atleta']}",
            minute=row["minuto"],
            penalty=row["tipo_de_gol"] == "Penalty",
            own_goal=row["tipo_de_gol"] == "Gol Contra",
        ))
    return goals


def read_cards(rows: TextIO, matches: dict[str, Match]) -> list[Card]:
    cards = []
    for row in csv.DictReader(rows):
        match = matches[row["partida_id"]]
        cards.append(Card(
            match_id=match.match_id,
            season=match.season,
            date=match.date,
            club=row["clube"],
            player=row["atleta"],
            player_ref=f"{SOURCE}:{row['atleta']}",
            red=row["cartao"] == "Vermelho",
        ))
    return cards


def load(cache: Path) -> Data:
    with open(cache / "campeonato-brasileiro-full.csv", encoding="utf-8") as rows:
        matches = read_matches(rows)
    with open(cache / "campeonato-brasileiro-gols.csv", encoding="utf-8") as rows:
        goals = read_goals(rows, matches)
    with open(cache / "campeonato-brasileiro-cartoes.csv", encoding="utf-8") as rows:
        cards = read_cards(rows, matches)
    return Data(matches, goals, cards)
