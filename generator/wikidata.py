"""Fetch footballers from Wikidata: language-page counts, names and aliases, and club stints.

Wikidata is never a source of prompt facts (its club histories have gaps). Stints are used only to
tell apart players who share a name.
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path

ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "futrivia/0.1 (https://github.com/felipemfp/futrivia)"
LANGS = ("pt", "pt-br", "en", "es", "mul")
CLUB_BATCH, NAME_BATCH, LABEL_BATCH = 25, 300, 25

Sparql = Callable[[str], list[dict]]


class WikidataError(Exception):
    pass


def http_sparql(query: str, tries: int = 4) -> list[dict]:
    data = urllib.parse.urlencode({"query": query, "format": "json"}).encode()
    for attempt in range(tries):
        try:
            request = urllib.request.Request(ENDPOINT, data=data, headers={
                "User-Agent": USER_AGENT, "Accept": "application/sparql-results+json"})
            with urllib.request.urlopen(request, timeout=90) as response:
                return json.load(response)["results"]["bindings"]
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            last = error
            time.sleep(20 * (attempt + 1))
    raise WikidataError(f"query failed after {tries} tries: {last!r}")


def _qid(binding: dict, key: str = "p") -> str:
    return binding[key]["value"].rsplit("/", 1)[1]


def _year(binding: dict, key: str) -> int | None:
    value = binding.get(key, {}).get("value", "")
    return int(value[:4]) if value[:4].isdigit() else None


def _literal(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _batches(items: list, size: int):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def _clubs_query() -> str:
    return """# clubs
SELECT DISTINCT ?c WHERE {
  ?c wdt:P31/wdt:P279* wd:Q476028; wdt:P17 wd:Q155.
  ?p wdt:P54 ?c; wdt:P106 wd:Q937857.
}"""


def _stints_query(clubs: list[str]) -> str:
    values = " ".join(f"wd:{c}" for c in clubs)
    # p:P54/ps:P54, never wdt:P54: wdt returns only preferred-rank clubs and hides past ones.
    return f"""# stints
SELECT ?p ?n ?teamLabel ?from ?to WHERE {{
  VALUES ?team {{ {values} }}
  ?p p:P54 ?st. ?st ps:P54 ?team. ?p wdt:P106 wd:Q937857; wikibase:sitelinks ?n.
  OPTIONAL {{ ?st pq:P580 ?from }} OPTIONAL {{ ?st pq:P582 ?to }}
  ?team rdfs:label ?teamLabel. FILTER(LANG(?teamLabel) = "pt")
}}"""


def _names_query(qids: list[str]) -> str:
    values = " ".join(f"wd:{q}" for q in qids)
    langs = ", ".join(f'"{lang}"' for lang in LANGS)
    return f"""# names
SELECT ?p ?l WHERE {{
  VALUES ?p {{ {values} }}
  {{ ?p rdfs:label ?l }} UNION {{ ?p skos:altLabel ?l }} UNION {{ ?p wdt:P1477 ?l }} UNION {{ ?p wdt:P1559 ?l }}
  FILTER(LANG(?l) IN ({langs}))
}}"""


def _labels_query(names: list[str]) -> str:
    values = " ".join(f"{_literal(name)}@{lang}" for name in names for lang in ("pt", "en", "es", "mul"))
    return f"""# labels
SELECT DISTINCT ?l ?p ?n WHERE {{
  VALUES ?l {{ {values} }}
  {{ ?p rdfs:label ?l }} UNION {{ ?p skos:altLabel ?l }}
  ?p wdt:P106 wd:Q937857; wikibase:sitelinks ?n.
}}"""


def fetch_people(sparql: Sparql, dataset_names: list[str]) -> dict:
    people: dict[str, dict] = {}

    def person(qid: str, sitelinks: int) -> dict:
        return people.setdefault(qid, {"sitelinks": sitelinks, "names": set(), "stints": set()})

    clubs = sorted({_qid(b, "c") for b in sparql(_clubs_query())})
    for batch in _batches(clubs, CLUB_BATCH):
        for b in sparql(_stints_query(batch)):
            person(_qid(b), int(b["n"]["value"]))["stints"].add((b["teamLabel"]["value"], _year(b, "from"), _year(b, "to")))
    for batch in _batches(sorted(people), NAME_BATCH):
        for b in sparql(_names_query(batch)):
            people[_qid(b)]["names"].add(b["l"]["value"])

    known = {name for p in people.values() for name in p["names"]}
    missing = sorted({n for n in dataset_names if n and n not in known})
    for batch in _batches(missing, LABEL_BATCH):
        for b in sparql(_labels_query(batch)):
            person(_qid(b), int(b["n"]["value"]))["names"].add(b["l"]["value"])

    return {
        qid: {"sitelinks": p["sitelinks"], "names": sorted(p["names"]),
              "stints": sorted([list(s) for s in p["stints"]], key=lambda s: (s[0], s[1] or 0, s[2] or 0))}
        for qid, p in sorted(people.items())
    }


def load_or_fetch(path: Path, sparql: Sparql, dataset_names: list[str], refresh: bool) -> dict:
    if path.exists() and not refresh:
        return json.loads(path.read_text(encoding="utf-8"))
    people = fetch_people(sparql, dataset_names)
    partial = path.with_suffix(".partial")
    partial.write_text(json.dumps(people, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    os.replace(partial, path)
    return people
