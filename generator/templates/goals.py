"""Goal-based prompt templates. Own goals never count as a player's goals."""
import itertools
from collections import Counter, defaultdict
from collections.abc import Iterable

from generator.records import Evidence, Goal, Match, PromptCandidate
from generator.text import contra, edition, pelo, slug, window, window_id

STOPPAGE_TIME_WINDOW = (2014, 2024)  # Transfermarkt files stoppage-time goals as minute 90, so only adaoduque has them


def _scored(goals: Iterable[Goal]) -> list[Goal]:
    return [g for g in goals if not g.own_goal]


def _in(goals: Iterable[Goal], span: tuple[int, int]) -> list[Goal]:
    return [g for g in goals if span[0] <= g.season <= span[1]]


def _answers(evidence: dict[str, list[Evidence]]) -> dict[str, tuple[Evidence, ...]]:
    return {ref: tuple(sorted(set(found), key=lambda e: (e[1], e[0]))) for ref, found in sorted(evidence.items())}


def hat_tricks(goals: list[Goal], spans: list[tuple[int, int]]) -> list[PromptCandidate]:
    prompts = []
    for span in spans:
        scored = _in(_scored(goals), span)
        per_match = Counter((g.match_id, g.player_ref) for g in scored)
        where = {(g.match_id, g.player_ref): (g.club, g.season) for g in scored}
        evidence: dict[str, list[Evidence]] = defaultdict(list)
        for key, count in sorted(per_match.items()):
            if count >= 3:
                evidence[key[1]].append(where[key])
        w = window(*span)
        prompts.append(PromptCandidate(
            id=f"hat-trick-{window_id(*span)}", template="hat-trick",
            text=f"Diga um jogador que marcou um hat-trick no Brasileirão, {w}",
            answers={ref: tuple(sorted(found, key=lambda e: (e[1], e[0]))) for ref, found in sorted(evidence.items())},
        ))
    return prompts


def scorers_for_club(goals: list[Goal], partial: dict[int, str]) -> list[PromptCandidate]:
    evidence: dict[tuple[str, int], dict[str, list[Evidence]]] = defaultdict(lambda: defaultdict(list))
    for g in _scored(goals):
        evidence[(g.club, g.season)][g.player_ref].append((g.club, g.season))
    return [PromptCandidate(
        id=f"marcou-por-{slug(club)}-{season}", template="marcou-por",
        text=f"Diga um jogador que marcou {pelo(club)} no Brasileirão {edition(season, partial)}",
        answers=_answers(found)) for (club, season), found in sorted(evidence.items())]


def scorers_against_club(goals: list[Goal], matches: dict[str, Match], partial: dict[int, str]) -> list[PromptCandidate]:
    evidence: dict[tuple[str, int], dict[str, list[Evidence]]] = defaultdict(lambda: defaultdict(list))
    for g in _scored(goals):
        m = matches[g.match_id]
        opponent = m.away if g.club == m.home else m.home
        evidence[(opponent, g.season)][g.player_ref].append((g.club, g.season))
    return [PromptCandidate(
        id=f"marcou-contra-{slug(club)}-{season}", template="marcou-contra",
        text=f"Diga um jogador que marcou {contra(club)} no Brasileirão {edition(season, partial)}",
        answers=_answers(found)) for (club, season), found in sorted(evidence.items())]


def _per_club(goals: Iterable[Goal], template: str, prefix: str, phrase: str, span: tuple[int, int]) -> list[PromptCandidate]:
    evidence: dict[str, dict[str, list[Evidence]]] = defaultdict(lambda: defaultdict(list))
    for g in goals:
        evidence[g.club][g.player_ref].append((g.club, g.season))
    return [PromptCandidate(
        id=f"{prefix}-{slug(club)}", template=template,
        text=f"Diga um jogador que marcou {phrase} {pelo(club)} no Brasileirão, {window(*span)}",
        answers=_answers(found)) for club, found in sorted(evidence.items())]


def penalty_scorers(goals: list[Goal], span: tuple[int, int]) -> list[PromptCandidate]:
    return _per_club([g for g in _in(_scored(goals), span) if g.penalty], "penalti", "penalti", "de pênalti", span)


def stoppage_time_scorers(goals: list[Goal]) -> list[PromptCandidate]:
    late = [g for g in _in(_scored(goals), STOPPAGE_TIME_WINDOW) if g.minute.startswith("90+")]
    return _per_club(late, "acrescimos", "acrescimos", "nos acréscimos do segundo tempo", STOPPAGE_TIME_WINDOW)


def prolific_seasons(goals: list[Goal], span: tuple[int, int], thresholds=(20, 18, 15, 12)) -> list[PromptCandidate]:
    per_season = Counter((g.player_ref, g.season) for g in _in(_scored(goals), span))
    clubs_of = defaultdict(set)
    for g in _in(_scored(goals), span):
        clubs_of[(g.player_ref, g.season)].add(g.club)
    prompts = []
    for n in thresholds:
        evidence: dict[str, list[Evidence]] = defaultdict(list)
        for (ref, season), count in per_season.items():
            if count >= n:
                evidence[ref].extend((club, season) for club in clubs_of[(ref, season)])
        prompts.append(PromptCandidate(
            id=f"gols-numa-edicao-{n}", template="gols-numa-edicao", family="gols-numa-edicao",
            text=f"Diga um jogador que fez {n} ou mais gols numa única edição do Brasileirão, {window(*span)}",
            answers=_answers(evidence)))
    return prompts


def club_totals(goals: list[Goal], span: tuple[int, int], thresholds=(20, 15, 10)) -> list[PromptCandidate]:
    scored = _in(_scored(goals), span)
    totals = Counter((g.club, g.player_ref) for g in scored)
    seasons = defaultdict(set)
    for g in scored:
        seasons[(g.club, g.player_ref)].add(g.season)
    prompts = []
    for club in sorted({g.club for g in scored}):
        for n in thresholds:
            evidence = {ref: [(c, s) for s in seasons[(c, ref)]] for (c, ref), total in totals.items() if c == club and total >= n}
            prompts.append(PromptCandidate(
                id=f"gols-por-{slug(club)}-{n}", template="gols-por", family=f"gols-por-{slug(club)}",
                text=f"Diga um jogador que fez {n} ou mais gols {pelo(club)} no Brasileirão, {window(*span)}",
                answers=_answers(evidence)))
    return prompts


def two_club_scorers(goals: list[Goal], span: tuple[int, int], clubs: Iterable[str]) -> list[PromptCandidate]:
    seen = defaultdict(lambda: defaultdict(set))
    for g in _in(_scored(goals), span):
        seen[g.player_ref][g.club].add(g.season)
    prompts = []
    for a, b in itertools.combinations(sorted(clubs), 2):
        evidence = {ref: [(a, s) for s in by_club[a]] + [(b, s) for s in by_club[b]]
                    for ref, by_club in seen.items() if by_club.get(a) and by_club.get(b)}
        prompts.append(PromptCandidate(
            id=f"marcou-por-{slug(a)}-e-{slug(b)}", template="marcou-por-dois",
            text=f"Diga um jogador que marcou {pelo(a)} e {pelo(b)} no Brasileirão, {window(*span)}",
            answers=_answers(evidence)))
    return prompts
