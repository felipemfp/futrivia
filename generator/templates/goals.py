"""Goal-based prompt templates. Own goals never count as a player's goals."""
from collections import Counter, defaultdict
from collections.abc import Iterable

from generator.records import Evidence, Goal, PromptCandidate


def _window(goals: Iterable[Goal]) -> str:
    seasons = [goal.season for goal in goals]
    first, last = min(seasons), max(seasons)
    return str(first) if first == last else f"{first}–{last}"


def hat_tricks(goals: list[Goal]) -> PromptCandidate:
    per_match = Counter((g.match_id, g.player_ref) for g in goals if not g.own_goal)
    where = {(g.match_id, g.player_ref): (g.club, g.season) for g in goals if not g.own_goal}
    evidence: dict[str, list[Evidence]] = defaultdict(list)
    for key, count in per_match.items():
        if count >= 3:
            evidence[key[1]].append(where[key])
    window = _window(goals)
    return PromptCandidate(
        id=f"hat-trick-{window}",
        template="hat-trick",
        text=f"Diga um jogador que marcou um hat-trick no Brasileirão, {window}",
        answers={ref: tuple(sorted(found, key=lambda e: (e[1], e[0]))) for ref, found in sorted(evidence.items())},
    )
