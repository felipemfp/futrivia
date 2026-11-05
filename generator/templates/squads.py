"""Card and lineup prompt templates. Lineups exist only for Brasileirão 2025 and 2026."""
from collections import Counter, defaultdict

from generator.records import Card, Evidence, LineupEntry, Match, PromptCandidate
from generator.text import edition, pelo, slug, window, window_id


def _answers(evidence: dict[str, list[Evidence]]) -> dict[str, tuple[Evidence, ...]]:
    return {ref: tuple(sorted(set(found), key=lambda e: (e[1], e[0]))) for ref, found in sorted(evidence.items())}


def red_cards(cards: list[Card], spans: list[tuple[int, int]]) -> list[PromptCandidate]:
    prompts = []
    for span in spans:
        evidence: dict[str, dict[str, list[Evidence]]] = defaultdict(lambda: defaultdict(list))
        for c in cards:
            if c.red and span[0] <= c.season <= span[1]:
                evidence[c.club][c.player_ref].append((c.club, c.season))
        w = window(*span)
        prompts += [PromptCandidate(
            id=f"expulso-{slug(club)}-{window_id(*span)}", template="expulso",
            text=f"Diga um jogador que foi expulso jogando {pelo(club)} no Brasileirão, {w}",
            answers=_answers(found)) for club, found in sorted(evidence.items())]
    return prompts


def clean_sheet_runs(lineups: list[LineupEntry], matches: dict[str, Match], partial: dict[int, str],
                     seasons=(2025,), thresholds=(5, 4, 3)) -> list[PromptCandidate]:
    keeper = {(e.match_id, e.club): e for e in lineups if e.starter and e.position == "Goalkeeper"}
    games = defaultdict(list)  # (season, club) -> [(date, match_id, conceded)]
    for m in matches.values():
        games[(m.season, m.home)].append((m.date, m.match_id, m.away_goals))
        games[(m.season, m.away)].append((m.date, m.match_id, m.home_goals))
    best = Counter()  # (ref, club, season) -> longest run
    for (season, club), played in games.items():
        run, previous = 0, None
        for _, match_id, conceded in sorted(played):
            entry = keeper.get((match_id, club))
            ref = entry.player_ref if entry else None
            run = (run + 1 if ref == previous else 1) if conceded == 0 and ref else 0
            previous = ref
            if ref:
                best[(ref, club, season)] = max(best[(ref, club, season)], run)
    prompts = []
    for season in seasons:
        for n in thresholds:
            evidence: dict[str, list[Evidence]] = defaultdict(list)
            for (ref, club, s), run in best.items():
                if s == season and run >= n:
                    evidence[ref].append((club, s))
            prompts.append(PromptCandidate(
                id=f"sem-sofrer-gol-{season}-{n}", template="sem-sofrer-gol", family=f"sem-sofrer-gol-{season}",
                text=f"Diga um goleiro que ficou {n} jogos seguidos sem sofrer gol no Brasileirão {edition(season, partial)}",
                answers=_answers(evidence)))
    return prompts


def starters(lineups: list[LineupEntry], partial: dict[int, str], thresholds=(1, 5, 10, 20)) -> list[PromptCandidate]:
    starts = Counter((e.club, e.season, e.player_ref) for e in lineups if e.starter)
    prompts = []
    for club, season in sorted({(c, s) for c, s, _ in starts}):
        for n in thresholds:
            evidence = {ref: [(club, season)] for (c, s, ref), count in starts.items() if (c, s) == (club, season) and count >= n}
            games = "" if n == 1 else f" em {n} ou mais jogos"
            prompts.append(PromptCandidate(
                id=f"titular-{slug(club)}-{season}-{n}", template="titular", family=f"titular-{slug(club)}-{season}",
                text=f"Diga um jogador que foi titular {pelo(club)}{games} no Brasileirão {edition(season, partial)}",
                answers=_answers(evidence)))
    return prompts
