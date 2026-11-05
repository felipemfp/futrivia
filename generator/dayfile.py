"""Day-file contract v1: the only link between the generator and the game. See SPEC.md."""
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

VERSION = 1
PROMPTS_PER_DAY = 7
MIN_ANSWERS, MAX_ANSWERS = 5, 40
TIERS = {"arquibancada": 10, "torcedor": 30, "raiz": 60, "resenha": 85, "enciclopedia": 100}


def normalize(text: str) -> str:
    """Must match normalize() in site/game/match.js; both are checked against tests/fixtures/normalize.json."""
    stripped = "".join(c for c in unicodedata.normalize("NFD", text) if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", stripped.lower()).split())


@dataclass(frozen=True)
class DayAnswer:
    id: str
    name: str
    aliases: tuple[str, ...]
    tier: str
    points: int
    evidence: str

    def to_json(self) -> dict:
        return {"id": self.id, "name": self.name, "aliases": list(self.aliases), "tier": self.tier,
                "points": self.points, "evidence": self.evidence}


@dataclass(frozen=True)
class DayPrompt:
    id: str
    text: str
    answers: tuple[DayAnswer, ...]

    def to_json(self) -> dict:
        return {"id": self.id, "text": self.text, "answers": [a.to_json() for a in self.answers]}


def validate(data: dict, expected_date: str) -> list[str]:
    errors = []
    if data.get("version") != VERSION:
        errors.append(f"version must be {VERSION}")
    if data.get("date") != expected_date:
        errors.append(f"date {data.get('date')!r} does not match file date {expected_date}")
    prompts = data.get("prompts", [])
    if len(prompts) != PROMPTS_PER_DAY:
        errors.append(f"day must have {PROMPTS_PER_DAY} prompts, has {len(prompts)}")
    prompt_ids = [p.get("id") for p in prompts]
    if len(set(prompt_ids)) != len(prompt_ids):
        errors.append("duplicate prompt id")
    for p in prompts:
        where = f"prompt {p.get('id')!r}"
        if not p.get("id") or not p.get("text"):
            errors.append(f"{where}: id and text are required")
        answers = p.get("answers", [])
        if not MIN_ANSWERS <= len(answers) <= MAX_ANSWERS:
            errors.append(f"{where}: needs {MIN_ANSWERS}–{MAX_ANSWERS} answers, has {len(answers)}")
        answer_ids = [a.get("id") for a in answers]
        if len(set(answer_ids)) != len(answer_ids):
            errors.append(f"{where}: duplicate answer id")
        for a in answers:
            who = f"{where}, answer {a.get('id')!r}"
            if not a.get("id") or not a.get("name"):
                errors.append(f"{who}: id and name are required")
            if a.get("tier") not in TIERS:
                errors.append(f"{who}: unknown tier {a.get('tier')!r}")
            elif a.get("points") != TIERS[a["tier"]]:
                errors.append(f"{who}: points {a.get('points')} do not match tier {a['tier']}")
            aliases = a.get("aliases") or []
            if not aliases:
                errors.append(f"{who}: needs at least one alias")
            for alias in aliases:
                if not alias or alias != normalize(alias):
                    errors.append(f"{who}: alias {alias!r} is empty or not normalized")
            if not isinstance(a.get("evidence"), str) or not a["evidence"]:
                errors.append(f"{who}: evidence is required")
    return errors


def write_day(directory: Path, date: str, prompts: list[DayPrompt]) -> Path:
    data = {"version": VERSION, "date": date, "prompts": [p.to_json() for p in prompts]}
    errors = validate(data, date)
    if errors:
        raise ValueError(f"{date}: " + "; ".join(errors))
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{date}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return path
