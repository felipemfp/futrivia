"""Checks against the pinned real data. Needs `python3 -m generator fetch` first."""
import collections
import unittest
from pathlib import Path

from generator.sources.adaoduque import load
from generator.templates.goals import hat_tricks

CACHE = Path(".cache")


class AdaoduqueRealDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (CACHE / "campeonato-brasileiro-full.csv").exists():
            raise RuntimeError("run `python3 -m generator fetch` before integration tests")
        cls.data = load(CACHE)

    def test_every_season_2014_2024_has_380_matches(self):
        per_season = collections.Counter(m.season for m in self.data.matches.values())
        # 2016 has 379: Chapecoense v Atlético-MG was never played after the Chapecoense air disaster.
        expected = {season: 380 for season in range(2014, 2025)} | {2016: 379}
        self.assertEqual({s: per_season[s] for s in expected}, expected)

    def test_goals_start_in_2014(self):
        self.assertEqual(min(g.season for g in self.data.goals), 2014)

    def test_hat_trick_counts_match_the_2026_11_05_test(self):
        prompt = hat_tricks(self.data.goals)
        self.assertEqual(len(prompt.answers), 36)
        self.assertEqual(sum(len(e) for e in prompt.answers.values()), 44)


if __name__ == "__main__":
    unittest.main()
