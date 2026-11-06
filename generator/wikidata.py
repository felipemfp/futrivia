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
SELECT ?p ?l ?k ?lang WHERE {{
  VALUES ?p {{ {values} }}
  {{ ?p rdfs:label ?l BIND("label" AS ?k) }} UNION {{ ?p skos:altLabel ?l BIND("alias" AS ?k) }}
  UNION {{ ?p wdt:P1477 ?l BIND("alias" AS ?k) }} UNION {{ ?p wdt:P1559 ?l BIND("alias" AS ?k) }}
  BIND(LANG(?l) AS ?lang) FILTER(?lang IN ({langs}))
}}"""


def _tmids_query(qids: list[str]) -> str:
    values = " ".join(f"wd:{q}" for q in qids)
    return f"""# tmids
SELECT ?p ?tm ?born WHERE {{
  VALUES ?p {{ {values} }}
  OPTIONAL {{ ?p wdt:P2446 ?tm }} OPTIONAL {{ ?p wdt:P569 ?born }}
}}"""


def _titles_query(qids: list[str]) -> str:
    values = " ".join(f"wd:{q}" for q in qids)
    return f"""# titles
SELECT ?p ?title WHERE {{
  VALUES ?p {{ {values} }}
  ?article schema:about ?p; schema:isPartOf <https://pt.wikipedia.org/>; schema:name ?title.
}}"""


def common_name(title: str) -> str:
    """'Maicon (futebolista, nascido em 1990)' -> 'Maicon': Portuguese Wikipedia titles use the name fans know."""
    return title.split(" (", 1)[0].strip()


def _bytm_query(ids: list[str]) -> str:
    values = " ".join(_literal(i) for i in ids)
    return f"""# bytm
SELECT ?p ?n ?tm WHERE {{ VALUES ?tm {{ {values} }} ?p wdt:P2446 ?tm; wikibase:sitelinks ?n. }}"""


def _labels_query(names: list[str]) -> str:
    values = " ".join(f"{_literal(name)}@{lang}" for name in names for lang in ("pt", "en", "es", "mul"))
    return f"""# labels
SELECT DISTINCT ?l ?p ?n WHERE {{
  VALUES ?l {{ {values} }}
  {{ ?p rdfs:label ?l }} UNION {{ ?p skos:altLabel ?l }}
  ?p wdt:P106 wd:Q937857; wikibase:sitelinks ?n.
}}"""


def _silent(stage: str, done: int, total: int) -> None:
    pass


def fetch_people(sparql: Sparql, dataset_names: list[str], transfermarkt_ids: list[str] = (),
                 progress: Callable[[str, int, int], None] = _silent) -> dict:
    people: dict[str, dict] = {}
    labels: dict[str, dict[str, str]] = {}
    titles: dict[str, str] = {}
    born: dict[str, int] = {}

    def batched(stage: str, items: list, size: int):
        batches = list(_batches(items, size))
        for number, batch in enumerate(batches, 1):
            yield batch
            progress(stage, number, len(batches))

    def person(qid: str, sitelinks: int) -> dict:
        return people.setdefault(qid, {"sitelinks": sitelinks, "names": set(), "stints": set(), "transfermarkt": set()})

    def add_details(qids: list[str]) -> None:
        for batch in batched("names", sorted(qids), NAME_BATCH):
            for b in sparql(_names_query(batch)):
                people[_qid(b)]["names"].add(b["l"]["value"])
                if b["k"]["value"] == "label":
                    labels.setdefault(_qid(b), {})[b["lang"]["value"]] = b["l"]["value"]
            for b in sparql(_tmids_query(batch)):
                if "tm" in b:
                    people[_qid(b)]["transfermarkt"].add(b["tm"]["value"])
                year = _year(b, "born")
                if year:
                    born[_qid(b)] = min(year, born.get(_qid(b), year))
            for b in sparql(_titles_query(batch)):
                titles[_qid(b)] = common_name(b["title"]["value"])

    clubs = sorted({_qid(b, "c") for b in sparql(_clubs_query())})
    for batch in batched("clubs", clubs, CLUB_BATCH):
        for b in sparql(_stints_query(batch)):
            person(_qid(b), int(b["n"]["value"]))["stints"].add((b["teamLabel"]["value"], _year(b, "from"), _year(b, "to")))
    add_details(list(people))

    # Players without a Brazilian club on Wikidata (its histories have gaps): look up by Transfermarkt id, then by name.
    before = set(people)
    known_tm = {i for p in people.values() for i in p["transfermarkt"]}
    for batch in batched("transfermarkt ids", sorted(set(transfermarkt_ids) - known_tm), LABEL_BATCH):
        for b in sparql(_bytm_query(batch)):
            person(_qid(b), int(b["n"]["value"]))["transfermarkt"].add(b["tm"]["value"])
    known = {name for p in people.values() for name in p["names"]}
    for batch in batched("labels", sorted({n for n in dataset_names if n and n not in known}), LABEL_BATCH):
        for b in sparql(_labels_query(batch)):
            person(_qid(b), int(b["n"]["value"]))["names"].add(b["l"]["value"])
    add_details(list(set(people) - before))

    def best_label(qid: str) -> str | None:
        found = labels.get(qid, {})
        return next((found[lang] for lang in LANGS if lang in found), None)

    return {
        qid: {"sitelinks": p["sitelinks"], "label": best_label(qid), "common": titles.get(qid), "born": born.get(qid),
              "names": sorted(p["names"]),
              "stints": sorted([list(s) for s in p["stints"]], key=lambda s: (s[0], s[1] or 0, s[2] or 0)),
              "transfermarkt": sorted(p["transfermarkt"])}
        for qid, p in sorted(people.items())
    }


def load_or_fetch(path: Path, sparql: Sparql, dataset_names: list[str], refresh: bool,
                  transfermarkt_ids: list[str] = (), progress: Callable[[str, int, int], None] = _silent) -> dict:
    if path.exists() and not refresh:
        return json.loads(path.read_text(encoding="utf-8"))
    people = fetch_people(sparql, dataset_names, transfermarkt_ids, progress)
    partial = path.with_suffix(".partial")
    partial.write_text(json.dumps(people, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    os.replace(partial, path)
    return people
