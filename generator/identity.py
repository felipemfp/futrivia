"""Give every dataset player one identity, so one person is one answer across sources and spellings.

Order: override file, Transfermarkt id, exact name with club and season, exact name alone, loose name with club.
Players without a single trusted match keep a "dataset:<name>" identity and no fame score.
"""
import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from generator.clubs import WIKIDATA_WORDS
from generator.dayfile import normalize

PARTICLES = {"de", "da", "do", "dos", "das", "e"}
SEASON_SLACK = 1  # Wikidata stint years are often off by one around transfer windows.


@dataclass(frozen=True)
class Player:
    ref: str
    name: str
    seen: frozenset[tuple[str, int]]  # (club key, season)


@dataclass(frozen=True)
class Override:
    ref: str
    wikidata: str | None  # None forces a dataset identity
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class Identity:
    id: str
    name: str
    aliases: tuple[str, ...]
    sitelinks: int | None
    status: str  # override, transfermarkt-id, club, name, ambiguous, none


def _words(text: str) -> set[str]:
    return set(normalize(text).split()) - PARTICLES


def _club_fits(club: str, season: int, stints: list, use_season: bool) -> bool:
    need = WIKIDATA_WORDS[club]
    for team, start, end in stints:
        if need <= _words(team):
            if not use_season:
                return True
            if (start is None or start - SEASON_SLACK <= season) and (end is None or season <= end + SEASON_SLACK):
                return True
    return False


def _pick_by_club(candidates: set[str], player: Player, people: dict) -> tuple[set[str], bool]:
    """Candidates whose club history fits the player's clubs, trying seasons first."""
    for use_season in (True, False):
        fit = {q for q in candidates
               if any(_club_fits(club, season, people[q]["stints"], use_season) for club, season in player.seen)}
        if fit:
            return fit, True
    return candidates, False


def read_overrides(path: Path) -> list[Override]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as rows:
        return [Override(r["ref"], r["wikidata"] or None, tuple(normalize(a) for a in r["aliases"].split("|") if a.strip()))
                for r in csv.DictReader(rows)]


def resolve(players: dict[str, Player], people: dict, overrides: list[Override]) -> tuple[dict[str, str], dict[str, Identity]]:
    by_name: dict[str, set[str]] = defaultdict(set)
    by_word: dict[str, set[str]] = defaultdict(set)
    by_tm: dict[str, set[str]] = defaultdict(set)
    for qid, p in people.items():
        for name in p["names"]:
            by_name[normalize(name)].add(qid)
            for word in _words(name):
                by_word[word].add(qid)
        for tm in p["transfermarkt"]:
            by_tm[tm].add(qid)
    override = {o.ref: o for o in overrides}

    def loose(player: Player) -> set[str]:
        typed = _words(player.name)
        if not typed:
            return set()
        pool = set.intersection(*(by_word.get(w, set()) for w in typed)) if len(typed) > 1 else by_word.get(next(iter(typed)), set())
        return {q for q in pool if any(len(typed & _words(n)) >= min(2, len(typed)) and (typed <= _words(n) or _words(n) <= typed)
                                       for n in people[q]["names"])}

    ref_to_id: dict[str, str] = {}
    status: dict[str, str] = {}
    extra_aliases: dict[str, set[str]] = defaultdict(set)

    def assign(ref: str, ident: str, how: str) -> None:
        ref_to_id[ref] = ident
        # One weak match never downgrades an identity another ref already established strongly.
        rank = ["none", "ambiguous", "name", "club", "transfermarkt-id", "override"]
        if ident not in status or rank.index(how) > rank.index(status[ident]):
            status[ident] = how

    for ref, player in sorted(players.items()):
        dataset_id = f"dataset:{player.name}"
        if ref in override:
            o = override[ref]
            if o.wikidata is not None and o.wikidata not in people:
                raise KeyError(f"override for {ref}: {o.wikidata} is not in the Wikidata cache")
            target = o.wikidata or dataset_id
            extra_aliases[target].update(o.aliases)
            assign(ref, target, "override")
            continue
        if ref.startswith("transfermarkt:"):
            found = by_tm.get(ref.split(":", 1)[1], set())
            if len(found) == 1:
                assign(ref, next(iter(found)), "transfermarkt-id")
                continue
        exact = by_name.get(normalize(player.name), set())
        if exact:
            fit, by_club = _pick_by_club(exact, player, people)
            if len(fit) == 1:
                assign(ref, next(iter(fit)), "club" if by_club else "name")
                continue
            assign(ref, dataset_id, "ambiguous")
            continue
        fit, by_club = _pick_by_club(loose(player), player, people)
        if by_club and len(fit) == 1:
            assign(ref, next(iter(fit)), "club")
            continue
        assign(ref, dataset_id, "ambiguous" if fit else "none")

    names_of: dict[str, set[str]] = defaultdict(set)
    for ref, ident in ref_to_id.items():
        names_of[ident].add(players[ref].name)

    identities = {}
    for ident, dataset_names in names_of.items():
        p = people.get(ident)
        aliases = {normalize(n) for n in dataset_names} | extra_aliases[ident]
        if p:
            aliases |= {normalize(n) for n in p["names"]}
        name = (p and p.get("label")) or min(dataset_names, key=len)
        identities[ident] = Identity(id=ident, name=name, aliases=tuple(sorted(a for a in aliases if a)),
                                     sitelinks=p["sitelinks"] if p else None, status=status[ident])
    return ref_to_id, identities
