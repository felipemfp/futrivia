import unittest

from generator.records import Card, LineupEntry, Match
from generator.templates import squads as t

PARTIAL = {2026: "até 1º de junho"}


def card(player, club="Santos", season=2023, red=True):
    return Card("m", season, f"{season}-06-01", club, player, f"t:{player}", red)


def start(match_id, date, player, club="Flamengo", position="Goalkeeper", starter=True, season=2025):
    return LineupEntry(match_id, season, date, club, player, f"t:{player}", position, starter)


def match(match_id, date, home, away, home_goals, away_goals, season=2025):
    return Match(match_id, season, date, home, away, home_goals, away_goals)


def answers(candidates, candidate_id):
    return set(next(c for c in candidates if c.id == candidate_id).answers)


class RedCardTest(unittest.TestCase):
    def test_only_red_cards_count(self):
        prompts = t.red_cards([card("A"), card("B", red=False)], [(2014, 2026)])
        self.assertEqual(answers(prompts, "expulso-santos-2014-2026"), {"t:A"})
        self.assertIn("foi expulso jogando pelo Santos", prompts[0].text)

    def test_window_ending_in_a_partial_season_says_where_the_data_stops(self):
        prompts = t.red_cards([card("A", season=2025)], [(2020, 2026)], PARTIAL)
        self.assertIn("2020–2026 (até 1º de junho)", prompts[0].text)

    def test_windows_split_by_season(self):
        prompts = t.red_cards([card("A", season=2015), card("B", season=2022)], [(2014, 2019), (2020, 2026)])
        self.assertEqual(answers(prompts, "expulso-santos-2014-2019"), {"t:A"})


class CleanSheetTest(unittest.TestCase):
    def setUp(self):
        # Flamengo concede 0, 0, 0, 1, 0, 0 with Rossi in goal, except a different keeper in match 6.
        scores = [(0, 0), (2, 0), (1, 0), (1, 1), (3, 0), (0, 0)]
        self.matches = {f"m{i}": match(f"m{i}", f"2025-0{i}-01", "Flamengo", "Santos", *s) for i, s in enumerate(scores, 1)}
        self.lineups = [start(f"m{i}", f"2025-0{i}-01", "Rossi" if i < 6 else "Matheus Cunha") for i in range(1, 7)]

    def test_run_counts_consecutive_clean_sheets_by_the_same_keeper(self):
        prompts = t.clean_sheet_runs(self.lineups, self.matches, PARTIAL, seasons=(2025,), thresholds=(3, 2))
        self.assertEqual(answers(prompts, "sem-sofrer-gol-2025-3"), {"t:Rossi"})

    def test_conceding_or_a_keeper_change_breaks_the_run(self):
        prompts = t.clean_sheet_runs(self.lineups, self.matches, PARTIAL, seasons=(2025,), thresholds=(4,))
        self.assertEqual(answers(prompts, "sem-sofrer-gol-2025-4"), set())

    def test_away_matches_count_the_home_side_goals(self):
        matches = {f"m{i}": match(f"m{i}", f"2025-0{i}-01", "Santos", "Flamengo", 0, 3) for i in range(1, 4)}
        lineups = [start(f"m{i}", f"2025-0{i}-01", "Rossi") for i in range(1, 4)]
        prompts = t.clean_sheet_runs(lineups, matches, PARTIAL, seasons=(2025,), thresholds=(3,))
        self.assertEqual(answers(prompts, "sem-sofrer-gol-2025-3"), {"t:Rossi"})

    def test_outfield_starters_are_ignored(self):
        lineups = self.lineups + [start("m1", "2025-01-01", "Léo Pereira", position="Centre-Back")]
        prompts = t.clean_sheet_runs(lineups, self.matches, PARTIAL, seasons=(2025,), thresholds=(1,))
        self.assertNotIn("t:Léo Pereira", answers(prompts, "sem-sofrer-gol-2025-1"))


class StartersTest(unittest.TestCase):
    def test_substitutes_are_not_starters(self):
        lineups = [start("m1", "2025-01-01", "A", position="Centre-Forward"),
                   start("m1", "2025-01-01", "B", position="Centre-Forward", starter=False)]
        prompts = t.starters(lineups, PARTIAL, thresholds=(1,))
        self.assertEqual(answers(prompts, "titular-flamengo-2025-1"), {"t:A"})

    def test_threshold_counts_starts(self):
        lineups = [start(f"m{i}", "2025-01-01", "A", position="Centre-Forward") for i in range(5)]
        lineups += [start("m9", "2025-01-01", "B", position="Centre-Forward")]
        prompts = t.starters(lineups, PARTIAL, thresholds=(1, 5))
        self.assertEqual(answers(prompts, "titular-flamengo-2025-5"), {"t:A"})
        self.assertIn("em 5 ou mais jogos", next(p for p in prompts if p.id == "titular-flamengo-2025-5").text)

    def test_partial_season_is_labelled(self):
        prompts = t.starters([start("m1", "2026-03-01", "A", season=2026)], PARTIAL, thresholds=(1,))
        self.assertIn("2026 (até 1º de junho)", prompts[0].text)


if __name__ == "__main__":
    unittest.main()
