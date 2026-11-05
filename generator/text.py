"""Portuguese wording helpers shared by templates."""
import re

from generator.clubs import display
from generator.dayfile import normalize

FEMININE = {"Chapecoense", "Ponte Preta"}


def pelo(club: str) -> str:
    return f"{'pela' if club in FEMININE else 'pelo'} {display(club)}"


def contra(club: str) -> str:
    return f"contra {'a' if club in FEMININE else 'o'} {display(club)}"


def window(first: int, last: int, partial: dict[int, str] | None = None) -> str:
    """'2014–2024', or '2020–2026 (até 1º de junho)' when the last season isn't covered in full."""
    text = str(first) if first == last else f"{first}–{last}"
    return f"{text} ({partial[last]})" if partial and last in partial else text


def window_id(first: int, last: int) -> str:
    return str(first) if first == last else f"{first}-{last}"


def edition(season: int, partial_seasons: dict[int, str]) -> str:
    """'2025', or '2026 (até 1º de junho)' for a season the data doesn't cover in full."""
    return f"{season} ({partial_seasons[season]})" if season in partial_seasons else str(season)


def slug(text: str) -> str:
    return re.sub(r"\s+", "-", normalize(text))
