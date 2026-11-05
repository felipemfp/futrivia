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
    name: str | None = None  # name shown to players, when the sources only have a legal name


@dataclass(frozen=True)
class Identity:
    id: str
    name: str
    aliases: tuple[str, ...]
    sitelinks: int | None
    status: str  # override, transfermarkt-id, club, name, ambiguous, none


def _words(text: str) -> set[str]:
    return set(normalize(text).split()) - PARTICLES


LEGAL_NAME_WORDS = 4
DIMINUTIVE_STEM = 4
PLAYING_AGES = range(15, 44)
NOT_A_NAME = {"futebolista", "futbolista", "footballer", "nascido", "nacido", "born", "fue", "eliminado", "jugador", "jogador"}
MAX_ALIAS_WORDS = 5
MAX_NICKNAME_CHARS = 12


def _plausible_age(person: dict, player: Player) -> bool:
    """A candidate must be of playing age in every season the dataset has the player."""
    born = person.get("born")
    return born is None or all(season - born in PLAYING_AGES for _, season in player.seen)


def _clean_aliases(names: list[str], known: list[str]) -> set[str]:
    """Wikidata aliases, minus vandalism and descriptions: an alias must share a word with a known name of the player,
    unless it is a single short nickname."""
    base = set().union(*(_words(n) for n in known)) if known else set()
    kept = set()
    for name in names:
        alias = normalize(name)
        words = alias.split()
        if not words or len(words) > MAX_ALIAS_WORDS or NOT_A_NAME & set(words):
            continue
        if _words(alias) & base or (len(words) == 1 and len(alias) <= MAX_NICKNAME_CHARS):
            kept.add(alias)
    return kept


def _shorten(name: str, candidates: list[str]) -> str:
    """A legal name ('André Luiz Paulino de Souza Motta') becomes the longest 1–2 word alias drawn from it ('André Paulino')."""
    if len(name.split()) < LEGAL_NAME_WORDS:
        return name
    full = _words(name)
    short = [c for c in candidates if 1 <= len(c.split()) <= 2 and _words(c) and _words(c) <= full]
    if not short:
        # A diminutive built on a word of the name: Rodrigo Eduardo Costa Marinho -> Rodriguinho.
        short = [c for c in candidates if len(c.split()) == 1 and _words(c)
                 and any(len(w) >= DIMINUTIVE_STEM and normalize(c).startswith(w[:DIMINUTIVE_STEM]) for w in full)]
    if not short:
        return name
    # More words first, then accented spellings over unaccented ones, then alphabetical for determinism.
    return max(short, key=lambda c: (len(c.split()), c != normalize(c), sum(1 for ch in c if ord(ch) > 127), c))


def _club_fits(club: str, season: int, stints: list, use_season: bool) -> bool:
    need = WIKIDATA_WORDS[club]
    for team, start, end in stints:
        if need <= _words(team):
            if not use_season:
                return True
            if (start is None or start - SEASON_SLACK <= season) and (end is None or season <= end + SEASON_SLACK):
                return True
    return False


def _confirmed_fits(seen: set[tuple[str, int]], club: str, season: int, use_season: bool) -> bool:
    return any(c == club and (not use_season or abs(s - season) <= SEASON_SLACK) for c, s in seen)


def _pick_by_club(candidates: set[str], player: Player, people: dict,
                  confirmed: dict[str, set[tuple[str, int]]] | None = None) -> tuple[set[str], bool]:
    """Candidates whose club history fits the player's clubs, trying seasons first. Clubs seen under a confirmed
    identity (Transfermarkt id, override) count as history too, and a confirmed candidate wins over unconfirmed ones."""
    confirmed = confirmed or {}
    for use_season in (True, False):
        fit = {q for q in candidates
               if any(_club_fits(club, season, people[q]["stints"], use_season)
                      or _confirmed_fits(confirmed.get(q, set()), club, season, use_season)
                      for club, season in player.seen)}
        sure = {q for q in fit if q in confirmed}
        if len(sure) == 1:
            return sure, True
        if fit:
            return fit, True
    return candidates, False


def read_overrides(path: Path) -> list[Override]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as rows:
        return [Override(r["ref"], r["wikidata"] or None, tuple(normalize(a) for a in r["aliases"].split("|") if a.strip()),
                         r.get("name") or None)
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
    shown_name: dict[str, str] = {}

    def assign(ref: str, ident: str, how: str) -> None:
        ref_to_id[ref] = ident
        # One weak match never downgrades an identity another ref already established strongly.
        rank = ["none", "ambiguous", "name", "club", "transfermarkt-id", "override"]
        if ident not in status or rank.index(how) > rank.index(status[ident]):
            status[ident] = how

    # Pass 1: identities we can trust outright (override file, Transfermarkt id).
    confirmed: dict[str, set[tuple[str, int]]] = defaultdict(set)  # qid -> (club, season) seen under it
    for ref, player in sorted(players.items()):
        dataset_id = f"dataset:{player.name}"
        if ref in override:
            o = override[ref]
            if o.wikidata is not None and o.wikidata not in people:
                raise KeyError(f"override for {ref}: {o.wikidata} is not in the Wikidata cache")
            target = o.wikidata or dataset_id
            extra_aliases[target].update(o.aliases)
            if o.name:
                shown_name[target] = o.name
            assign(ref, target, "override")
        elif ref.startswith("transfermarkt:") and len(found := by_tm.get(ref.split(":", 1)[1], set())) == 1:
            assign(ref, next(iter(found)), "transfermarkt-id")
        else:
            continue
        if ref_to_id[ref] in people:
            confirmed[ref_to_id[ref]] |= player.seen
            by_name[normalize(player.name)].add(ref_to_id[ref])

    # Pass 2: everyone else, by name and club. Confirmed people skip the age check: their Wikidata birth year can be
    # wrong (Luciano's says 1965) while the Transfermarkt id is certain.
    def plausible(q: str, player: Player) -> bool:
        return q in confirmed or _plausible_age(people[q], player)

    for ref, player in sorted(players.items()):
        if ref in ref_to_id:
            continue
        dataset_id = f"dataset:{player.name}"
        exact = {q for q in by_name.get(normalize(player.name), set()) if plausible(q, player)}
        if exact:
            fit, by_club = _pick_by_club(exact, player, people, confirmed)
            if len(fit) == 1:
                assign(ref, next(iter(fit)), "club" if by_club else "name")
                continue
            assign(ref, dataset_id, "ambiguous")
            continue
        fit, by_club = _pick_by_club({q for q in loose(player) if plausible(q, player)}, player, people, confirmed)
        if by_club and len(fit) == 1:
            assign(ref, next(iter(fit)), "club")
            continue
        assign(ref, dataset_id, "ambiguous" if fit else "none")

    # Pass 3: a short name left ambiguous ("Marinho") joins a person whose other spelling ("Mário Sérgio Santos Costa")
    # resolved in pass 2 at the same club and season, if exactly one such person shares the name.
    resolved_seen: dict[str, set[tuple[str, int]]] = defaultdict(set)
    for ref, ident in ref_to_id.items():
        if ident in people:
            resolved_seen[ident] |= players[ref].seen
    for ref, player in sorted(players.items()):
        if ref_to_id[ref] in people or ref in override:
            continue
        near = {q for q in by_name.get(normalize(player.name), set())
                if any(_confirmed_fits(resolved_seen[q], club, season, True) for club, season in player.seen)}
        if len(near) == 1:
            assign(ref, next(iter(near)), "club")

    names_of: dict[str, set[str]] = defaultdict(set)
    transfermarkt_names: dict[str, set[str]] = defaultdict(set)
    for ref, ident in ref_to_id.items():
        names_of[ident].add(players[ref].name)
        if ref.startswith("transfermarkt:"):
            transfermarkt_names[ident].add(players[ref].name)

    identities = {}
    for ident, dataset_names in names_of.items():
        p = people.get(ident)
        known = [n for n in sorted(transfermarkt_names[ident]) + [p and p.get("common"), p and p.get("label")]
                 + sorted(dataset_names) if n and n.split(" (", 1)[0].strip()]  # sources hold some blank names
        aliases = {normalize(n) for n in dataset_names} | extra_aliases[ident]
        if p:
            aliases |= _clean_aliases(p["names"], known)
        # Shown name: the override, else the shortest name the sources use for the player. Labels and Wikipedia
        # titles are each sometimes a legal name (Frederico Chaves Guedes for Fred), so neither wins outright.
        if ident in shown_name:
            name = shown_name[ident]
        else:
            name = min(known, key=lambda n: (len(n.split(" (", 1)[0].split()), known.index(n)))
            name = _shorten(name, (p["names"] if p else []) + sorted(dataset_names))
        name = name.split(" (", 1)[0].strip()  # 'Carlos Júnior (futebolista)': disambiguation isn't part of the name
        aliases.add(normalize(name))
        identities[ident] = Identity(id=ident, name=name, aliases=tuple(sorted(a for a in aliases if a)),
                                     sitelinks=p["sitelinks"] if p else None, status=status[ident])
    return ref_to_id, identities
