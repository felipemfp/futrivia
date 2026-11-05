import datetime
import unittest

from generator.build import ScheduleError, collect_players, format_evidence, prepare, schedule
from generator.dayfile import DayAnswer, DayPrompt
from generator.identity import Identity
from generator.records import PromptCandidate


def identity(qid, sitelinks=10, status="club"):
    return Identity(qid, f"Nome {qid}", (f"nome {qid.lower()}",), sitelinks, status)


IDS = {f"Q{i}": identity(f"Q{i}", sitelinks=100 - i) for i in range(50)}
REFS = {f"r{i}": f"Q{i}" for i in range(50)} | {"r0-other-spelling": "Q0"}


def candidate(id_, refs, family="", template="t"):
    return PromptCandidate(id=id_, template=template, text=f"Texto {id_}", family=family,
                           answers={r: (("Santos", 2019),) for r in refs})


class PrepareTest(unittest.TestCase):
    def prepare(self, candidates, trusted=lambda i: True):
        return prepare(candidates, REFS, IDS, trusted)

    def test_two_refs_of_one_person_are_one_answer(self):
        kept, _ = self.prepare([candidate("p", ["r0", "r0-other-spelling", "r1", "r2", "r3", "r4"])])
        self.assertEqual(len(kept[0].prompt.answers), 5)

    def test_prompts_outside_5_to_40_answers_are_dropped_and_counted(self):
        kept, report = self.prepare([candidate("few", ["r1", "r2", "r3", "r4"]),
                                     candidate("many", [f"r{i}" for i in range(41)]),
                                     candidate("ok", [f"r{i}" for i in range(5)])])
        self.assertEqual([k.prompt.id for k in kept], ["ok"])
        self.assertEqual(report["t"], {"candidates": 3, "kept": 1, "too_few": 1, "too_many": 1})

    def test_family_keeps_only_its_first_variant_that_fits(self):
        kept, _ = self.prepare([candidate("f-40", [f"r{i}" for i in range(3)], family="f"),
                                candidate("f-30", [f"r{i}" for i in range(6)], family="f"),
                                candidate("f-20", [f"r{i}" for i in range(9)], family="f")])
        self.assertEqual([k.prompt.id for k in kept], ["f-30"])

    def test_answers_are_ordered_obvious_first_with_tier_points(self):
        kept, _ = self.prepare([candidate("p", ["r4", "r0", "r2", "r1", "r3"])])
        answers = kept[0].prompt.answers
        self.assertEqual([a.id for a in answers], ["Q0", "Q1", "Q2", "Q3", "Q4"])
        self.assertEqual([a.points for a in answers], [10, 30, 60, 85, 100])

    def test_untrusted_identities_get_the_default_tier(self):
        kept, _ = self.prepare([candidate("p", ["r0", "r1", "r2", "r3", "r4"])], trusted=lambda i: i.id != "Q0")
        self.assertEqual(next(a for a in kept[0].prompt.answers if a.id == "Q0").tier, "raiz")


class CollectPlayersTest(unittest.TestCase):
    def test_own_goal_club_is_not_evidence_of_where_the_player_played(self):
        from generator.records import Goal
        own = Goal("m", 2023, "2023-06-01", "Flamengo", "Léo", "t:Léo", "10", False, True)
        players = collect_players([own], [], [])
        self.assertEqual(players["t:Léo"].seen, frozenset())

    def test_only_players_in_the_records_are_collected(self):
        from generator.records import Card
        players = collect_players([], [Card("m", 2023, "2023-06-01", "Santos", "A", "t:A", True)], [])
        self.assertEqual(list(players), ["t:A"])


class EvidenceTest(unittest.TestCase):
    def test_formats_clubs_with_accents_and_caps_the_list(self):
        evidence = [("Gremio", 2023), ("Santos", 2018), ("Santos", 2019), ("Sao Paulo", 2020)]
        self.assertEqual(format_evidence(evidence), "Santos 2018, Santos 2019, São Paulo 2020 e mais 1")


def day_prompt(i, template):
    return DayPrompt(f"p{i}", f"Texto {i}", tuple(DayAnswer(f"Q{j}", "N", ("n",), "raiz", 60, "e") for j in range(5)))


class ScheduleTest(unittest.TestCase):
    def pool(self, n, templates=4):
        from generator.build import Prepared
        return [Prepared(day_prompt(i, f"t{i % templates}"), f"t{i % templates}") for i in range(n)]

    def test_fills_every_day_with_7_distinct_prompts_and_at_most_2_per_template(self):
        days = schedule(self.pool(70), datetime.date(2027, 1, 1), 10, seed="s")
        self.assertEqual(len(days), 10)
        seen = [p.prompt.id for prompts in days.values() for p in prompts]
        self.assertEqual(len(seen), len(set(seen)))
        for prompts in days.values():
            self.assertEqual(len(prompts), 7)
            counts = {}
            for p in prompts:
                counts[p.template] = counts.get(p.template, 0) + 1
            self.assertLessEqual(max(counts.values()), 2)

    def test_same_seed_gives_the_same_schedule(self):
        first = schedule(self.pool(70), datetime.date(2027, 1, 1), 10, seed="s")
        second = schedule(list(reversed(self.pool(70))), datetime.date(2027, 1, 1), 10, seed="s")
        self.assertEqual({d: [p.prompt.id for p in ps] for d, ps in first.items()},
                         {d: [p.prompt.id for p in ps] for d, ps in second.items()})

    def test_too_few_prompts_reports_the_real_number(self):
        with self.assertRaisesRegex(ScheduleError, "69 prompts"):
            schedule(self.pool(69), datetime.date(2027, 1, 1), 10, seed="s")

    def test_too_few_templates_to_respect_the_daily_limit_fails(self):
        with self.assertRaises(ScheduleError):
            schedule(self.pool(70, templates=3), datetime.date(2027, 1, 1), 10, seed="s")


if __name__ == "__main__":
    unittest.main()
