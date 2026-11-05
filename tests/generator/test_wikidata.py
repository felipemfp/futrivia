import json
import tempfile
import unittest
from pathlib import Path

from generator import wikidata


def uri(qid: str) -> dict:
    return {"type": "uri", "value": f"http://www.wikidata.org/entity/{qid}"}


def lit(value: str) -> dict:
    return {"type": "literal", "value": value}


class FakeSparql:
    """Answers each query kind from canned bindings and records the queries it saw."""

    def __init__(self, clubs=(), stints=(), names=(), labels=(), fail_on: str | None = None):
        self.responses = {"clubs": list(clubs), "stints": list(stints), "names": list(names), "labels": list(labels)}
        self.fail_on = fail_on
        self.queries: list[tuple[str, str]] = []

    def __call__(self, query: str) -> list[dict]:
        kind = query.split("\n", 1)[0].removeprefix("# ").strip()
        self.queries.append((kind, query))
        if kind == self.fail_on:
            raise wikidata.WikidataError(f"{kind} failed")
        return self.responses[kind]


RODRYGO_STINTS = [
    {"p": uri("Q42728914"), "n": lit("61"), "teamLabel": lit("Santos Futebol Clube"), "from": lit("2017-01-01T00:00:00Z"), "to": lit("2019-07-01T00:00:00Z")},
    {"p": uri("Q42728914"), "n": lit("61"), "teamLabel": lit("Seleção Brasileira de Futebol"), "from": lit("2019-01-01T00:00:00Z")},
]
RODRYGO_NAMES = [
    {"p": uri("Q42728914"), "l": lit("Rodrygo")},
    {"p": uri("Q42728914"), "l": lit("Rodrygo Silva de Goes")},
]


class WikidataTest(unittest.TestCase):
    def fetch(self, sparql: FakeSparql, names=()) -> dict:
        return wikidata.fetch_people(sparql, list(names))

    def test_club_history_uses_all_statements_not_only_preferred_rank(self):
        # Regression: wdt:P54 returns only preferred-rank clubs, which hid Rodrygo's Santos years.
        sparql = FakeSparql(clubs=[{"c": uri("Q80955")}], stints=RODRYGO_STINTS, names=RODRYGO_NAMES)
        self.fetch(sparql)
        stint_query = next(q for kind, q in sparql.queries if kind == "stints")
        self.assertIn("p:P54", stint_query)
        self.assertNotIn("wdt:P54", stint_query)

    def test_person_gets_names_stints_and_sitelinks(self):
        sparql = FakeSparql(clubs=[{"c": uri("Q80955")}], stints=RODRYGO_STINTS, names=RODRYGO_NAMES)
        person = self.fetch(sparql)["Q42728914"]
        self.assertEqual(person["sitelinks"], 61)
        self.assertEqual(person["names"], ["Rodrygo", "Rodrygo Silva de Goes"])
        self.assertIn(["Santos Futebol Clube", 2017, 2019], person["stints"])
        self.assertIn(["Seleção Brasileira de Futebol", 2019, None], person["stints"])

    def test_names_not_found_among_brazilian_club_players_are_looked_up_by_label(self):
        labels = [{"l": lit("Lucas Pratto", ), "p": uri("Q1845684"), "n": lit("23")}]
        sparql = FakeSparql(clubs=[{"c": uri("Q80955")}], stints=RODRYGO_STINTS, names=RODRYGO_NAMES, labels=labels)
        people = self.fetch(sparql, names=["Rodrygo", "Lucas Pratto"])
        label_query = next(q for kind, q in sparql.queries if kind == "labels")
        self.assertIn('"Lucas Pratto"@pt', label_query)
        self.assertNotIn('"Rodrygo"@pt', label_query)
        self.assertEqual(people["Q1845684"]["sitelinks"], 23)
        self.assertEqual(people["Q1845684"]["stints"], [])

    def test_label_lookup_is_batched(self):
        names = [f"Jogador {i}" for i in range(60)]
        sparql = FakeSparql(clubs=[{"c": uri("Q80955")}])
        self.fetch(sparql, names=names)
        self.assertEqual(sum(1 for kind, _ in sparql.queries if kind == "labels"), 3)

    def test_quotes_in_names_are_escaped(self):
        sparql = FakeSparql(clubs=[{"c": uri("Q80955")}])
        self.fetch(sparql, names=['Jogador "X"'])
        label_query = next(q for kind, q in sparql.queries if kind == "labels")
        self.assertIn('"Jogador \\"X\\""@pt', label_query)

    def test_any_failed_query_fails_the_whole_fetch(self):
        sparql = FakeSparql(clubs=[{"c": uri("Q80955")}], stints=RODRYGO_STINTS, fail_on="names")
        with self.assertRaises(wikidata.WikidataError):
            self.fetch(sparql)


class CacheTest(unittest.TestCase):
    def test_fetch_writes_cache_and_later_runs_reuse_it(self):
        sparql = FakeSparql(clubs=[{"c": uri("Q80955")}], stints=RODRYGO_STINTS, names=RODRYGO_NAMES)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wikidata.json"
            wikidata.load_or_fetch(path, sparql, [], refresh=False)
            calls = len(sparql.queries)
            people = wikidata.load_or_fetch(path, sparql, [], refresh=False)
            self.assertEqual(len(sparql.queries), calls)
            self.assertIn("Q42728914", people)

    def test_failed_fetch_leaves_previous_cache_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wikidata.json"
            path.write_text(json.dumps({"Q1": {"sitelinks": 1, "names": ["A"], "stints": []}}))
            with self.assertRaises(wikidata.WikidataError):
                wikidata.load_or_fetch(path, FakeSparql(fail_on="clubs"), [], refresh=True)
            self.assertIn("Q1", json.loads(path.read_text()))


if __name__ == "__main__":
    unittest.main()
