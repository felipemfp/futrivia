"""Checks against the pinned real data. Needs `python3 -m generator fetch` first."""
import collections
import unittest
from pathlib import Path

from generator import clubs
from generator.sources import transfermarkt
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
        prompt = hat_tricks(self.data.goals, [(2014, 2024)])[0]
        self.assertEqual(len(prompt.answers), 36)
        self.assertEqual(sum(len(e) for e in prompt.answers.values()), 44)

    def test_every_club_has_a_display_name(self):
        for club in {g.club for g in self.data.goals} | {c.club for c in self.data.cards}:
            self.assertTrue(clubs.display(club), club)


class TransfermarktRealDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = transfermarkt.load(CACHE)

    def test_seasons_are_brasileirao_2025_full_and_2026_partial(self):
        per_season = collections.Counter(m.season for m in self.data.matches.values())
        self.assertEqual(dict(per_season), {2025: 380, 2026: 177})
        self.assertEqual(max(m.date for m in self.data.matches.values() if m.season == 2025), "2025-12-07")

    def test_goal_events_add_up_to_every_final_score(self):
        per_club = collections.Counter((g.match_id, g.club) for g in self.data.goals)
        for m in self.data.matches.values():
            self.assertEqual((per_club[(m.match_id, m.home)], per_club[(m.match_id, m.away)]),
                             (m.home_goals, m.away_goals), m.match_id)

    def test_neymar_is_in_the_data(self):
        neymar = "transfermarkt:68290"
        self.assertEqual(self.data.names[neymar], "Neymar")
        self.assertEqual(sum(1 for e in self.data.lineups if e.player_ref == neymar), 28)
        self.assertEqual(sum(1 for g in self.data.goals if g.player_ref == neymar and not g.own_goal), 12)


if __name__ == "__main__":
    unittest.main()
