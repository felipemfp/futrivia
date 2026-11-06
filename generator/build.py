"""Build day files: templates → identity-merged answers → rarity tiers → schedule → site/days/*.json."""
import dataclasses
import datetime
import hashlib
import json
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from generator import config
from generator.clubs import display
from generator.dayfile import MAX_ANSWERS, MIN_ANSWERS, PROMPTS_PER_DAY, TIERS, DayAnswer, DayPrompt, normalize, write_day
from generator.identity import Identity, Player, read_overrides, resolve
from generator.rarity import ORDER, assign_tiers
from generator.records import Evidence, PromptCandidate
from generator.sources import adaoduque, transfermarkt
from generator.templates import goals as goal_templates
from generator.templates import squads as squad_templates

MAX_PER_TEMPLATE_PER_DAY = 2
EVIDENCE_SHOWN = 3
MONTHS = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro",
          "novembro", "dezembro"]


class ScheduleError(Exception):
    pass


@dataclass(frozen=True)
class Prepared:
    prompt: DayPrompt
    template: str


def format_evidence(evidence: list[Evidence]) -> str:
    ordered = sorted(set(evidence), key=lambda e: (e[1], e[0]))
    shown = ", ".join(f"{display(club)} {season}" for club, season in ordered[:EVIDENCE_SHOWN])
    rest = len(ordered) - EVIDENCE_SHOWN
    return f"{shown} e mais {rest}" if rest > 0 else shown


def _join_unresolved_namesakes(merged: dict[str, list[Evidence]], identities: dict[str, Identity]) -> None:
    """Within one prompt, an unresolved per-club identity ('dataset:Fred|Atletico-MG') sharing its shown name with
    another answer joins it: it is almost always the same player at a club Wikidata doesn't list, and two answers
    with one name could never be told apart by typing. Two resolved people keep separate answers."""
    by_name: dict[str, list[str]] = defaultdict(list)
    for ident in sorted(merged):
        by_name[normalize(identities[ident].name)].append(ident)
    for group in by_name.values():
        resolved = [i for i in group if not i.startswith("dataset:")]
        unresolved = [i for i in group if i.startswith("dataset:")]
        if len(group) < 2 or not unresolved or len(resolved) > 1:
            continue
        target = resolved[0] if resolved else unresolved[0]
        for ident in unresolved:
            if ident != target:
                merged[target].extend(merged.pop(ident))


def prepare(candidates: list[PromptCandidate], ref_to_id: dict[str, str], identities: dict[str, Identity],
            trusted: Callable[[Identity], bool]) -> tuple[list[Prepared], dict]:
    report: dict[str, Counter] = defaultdict(Counter)
    done_families: set[str] = set()
    seen_sets: set[tuple[str, frozenset]] = set()
    kept = []
    for c in candidates:
        stats = report[c.template]
        stats["candidates"] += 1
        if c.family and c.family in done_families:
            continue
        merged: dict[str, list[Evidence]] = defaultdict(list)
        for ref, evidence in c.answers.items():
            ident = ref_to_id.get(ref, ref)  # canonical records already carry identity ids
            if identities[ident].name:  # nobody can type a player the sources never named
                merged[ident].extend(evidence)
        _join_unresolved_namesakes(merged, identities)
        if len(merged) < MIN_ANSWERS:
            stats["too_few"] += 1
            continue
        if len(merged) > MAX_ANSWERS:
            stats["too_many"] += 1
            continue
        answer_set = (c.template, frozenset(merged))
        if answer_set in seen_sets:  # e.g. a club that only played in one era gives the same list for two windows
            stats["duplicate"] += 1
            continue
        seen_sets.add(answer_set)
        if c.family:
            done_families.add(c.family)
        fame = {i: (identities[i].sitelinks if trusted(identities[i]) else None) for i in merged}
        tiers = assign_tiers(fame)
        answers = sorted(merged, key=lambda i: (ORDER.index(tiers[i]), -(fame[i] or 0), identities[i].name))
        kept.append(Prepared(DayPrompt(c.id, c.text, tuple(
            DayAnswer(i, identities[i].name, identities[i].aliases, tiers[i], TIERS[tiers[i]], format_evidence(merged[i]))
            for i in answers)), c.template))
        stats["kept"] += 1
    return kept, {t: {k: s[k] for k in ("candidates", "kept", "too_few", "too_many", "duplicate")} for t, s in sorted(report.items())}


def _order_key(seed: str, prompt_id: str) -> str:
    return hashlib.sha256(f"{seed}:{prompt_id}".encode()).hexdigest()


def _fill(pool: list[Prepared], start: datetime.date, limit: int, seed: str) -> dict[str, list[Prepared]]:
    """Schedule up to `limit` days, stopping at the first day that can't be filled within the template limit."""
    queues: dict[str, list[Prepared]] = defaultdict(list)
    for p in sorted(pool, key=lambda p: _order_key(seed, p.prompt.id)):
        queues[p.template].append(p)
    result = {}
    for offset in range(limit):
        date = (start + datetime.timedelta(days=offset)).isoformat()
        # Draw from the fullest templates first, so no template runs dry while others pile up.
        picked = []
        for template in sorted(queues, key=lambda t: (-len(queues[t]), t)):
            take = min(MAX_PER_TEMPLATE_PER_DAY, len(queues[template]), PROMPTS_PER_DAY - len(picked))
            picked += [queues[template].pop(0) for _ in range(take)]
        if len(picked) < PROMPTS_PER_DAY:
            break
        result[date] = sorted(picked, key=lambda p: _order_key(f"{seed}:{date}", p.prompt.id))
    return result


def schedulable_days(pool: list[Prepared], seed: str) -> int:
    return len(_fill(pool, datetime.date(2000, 1, 1), len(pool) // PROMPTS_PER_DAY, seed))


def schedule(pool: list[Prepared], start: datetime.date, days: int, seed: str) -> dict[str, list[Prepared]]:
    needed = days * PROMPTS_PER_DAY
    if len(pool) < needed:
        raise ScheduleError(f"{days} days need {needed} prompts; only {len(pool)} prompts pass the filters "
                            f"({schedulable_days(pool, seed)} days can be scheduled)")
    result = _fill(pool, start, days, seed)
    if len(result) < days:
        raise ScheduleError(f"only {len(result)} of {days} days can be filled with at most "
                            f"{MAX_PER_TEMPLATE_PER_DAY} prompts per template a day")
    return result


def _partial_seasons(matches) -> dict[int, str]:
    last = defaultdict(str)
    for m in matches:
        last[m.season] = max(last[m.season], m.date)
    partial = {}
    for season, date in last.items():
        day = datetime.date.fromisoformat(date)
        if day.month < 11:  # every complete season ends in November or December
            partial[season] = f"até {'1º' if day.day == 1 else day.day} de {MONTHS[day.month - 1]}"
    return partial


def collect_players(goals, cards, lineups) -> dict[str, Player]:
    """Every player in the Série A records, with the (club, season) pairs they were seen at."""
    seen = defaultdict(set)
    name_of = {}
    for g in goals:
        if not g.own_goal:  # an own goal is filed under the opponent club
            seen[g.player_ref].add((g.club, g.season))
        name_of.setdefault(g.player_ref, g.player)
    for record in [*cards, *lineups]:
        seen[record.player_ref].add((record.club, record.season))
        name_of.setdefault(record.player_ref, record.player)
    return {ref: Player(ref, name_of[ref], frozenset(seen[ref])) for ref in sorted(name_of)}


def canonical(records: list, ref_to_id: dict[str, str]) -> list:
    """Records keyed by person, not by source: thresholds and 'both clubs' must count one player once."""
    return [dataclasses.replace(r, player_ref=ref_to_id[r.player_ref]) for r in records]


def candidates_from(old, new, ref_to_id: dict[str, str]) -> list[PromptCandidate]:
    goals = canonical(old.goals + new.goals, ref_to_id)
    cards = canonical(old.cards + new.cards, ref_to_id)
    lineups = canonical(new.lineups, ref_to_id)
    matches = {**old.matches, **new.matches}
    partial = _partial_seasons(new.matches.values())
    span = (min(g.season for g in goals), max(g.season for g in goals))
    eras = [span, (span[0], 2019), (2020, span[1])]
    regular_clubs = [c for c, n in Counter(club for club, _ in {(g.club, g.season) for g in goals}).items() if n >= 8]
    return [
        *goal_templates.hat_tricks(goals, eras, partial),
        *goal_templates.scorers_for_club(goals, partial),
        *goal_templates.scorers_against_club(goals, matches, partial),
        *goal_templates.penalty_scorers(goals, span, partial),
        *goal_templates.stoppage_time_scorers(goals),
        *goal_templates.prolific_seasons(goals, span, partial=partial),
        *goal_templates.club_totals(goals, span, partial=partial),
        *goal_templates.two_club_scorers(goals, span, regular_clubs, partial),
        *squad_templates.red_cards(cards, eras, partial),
        *squad_templates.clean_sheet_runs(lineups, new.matches, partial, seasons=(2025,)),
        *squad_templates.starters(lineups, partial),
    ]


def trusted(identity: Identity) -> bool:
    if identity.sitelinks is None:
        return False
    return identity.status != "name" or config.NAME_ONLY_TRUSTED


def build(cache: Path, overrides: Path, out: Path, report_path: Path, start: datetime.date, days: int) -> dict:
    people_path = cache / "wikidata.json"
    if not people_path.exists():
        raise FileNotFoundError("run `python3 -m generator wikidata` first")
    old, new = adaoduque.load(cache), transfermarkt.load(cache)
    players = collect_players(old.goals + new.goals, old.cards + new.cards, new.lineups)
    ref_to_id, identities = resolve(players, json.loads(people_path.read_text(encoding="utf-8")), read_overrides(overrides))
    pool, per_template = prepare(candidates_from(old, new, ref_to_id), ref_to_id, identities, trusted)

    statuses = Counter(identities[i].status for i in set(ref_to_id.values()))
    in_use = {a.id for p in pool for a in p.prompt.answers}
    report = {
        "start": start.isoformat(), "days": days, "prompts_available": len(pool),
        "prompts_needed": days * PROMPTS_PER_DAY,
        "days_schedulable": schedulable_days(pool, config.SCHEDULE_SEED),
        "templates": per_template,
        "identities": dict(sorted(statuses.items())),
        "answers_in_use": len(in_use),
        "answers_untrusted": sum(1 for i in in_use if not trusted(identities[i])),
        "name_only_trusted": config.NAME_ONLY_TRUSTED,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        days_out = schedule(pool, start, days, config.SCHEDULE_SEED)
    except ScheduleError as error:
        report["error"] = str(error)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        raise
    for date, prompts in days_out.items():
        write_day(out, date, [p.prompt for p in prompts])
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return report
