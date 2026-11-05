import unittest

from generator.records import Goal, Match
from generator.templates import goals as t

PARTIAL = {2026: "até 1º de junho"}


def goal(match, player, club="Gremio", season=2023, own_goal=False, penalty=False, minute="10"):
    return Goal(match_id=match, season=season, date=f"{season}-06-01", club=club, player=player,
                player_ref=f"t:{player}", minute=minute, penalty=penalty, own_goal=own_goal)


def match(match_id, home, away, season=2023):
    return Match(match_id, season, f"{season}-06-01", home, away, 0, 0)


def answers(candidates, candidate_id):
    return set(next(c for c in candidates if c.id == candidate_id).answers)


class HatTrickTest(unittest.TestCase):
    def test_three_goals_in_one_match_is_a_hat_trick(self):
        prompts = t.hat_tricks([goal("m1", "A")] * 3, [(2014, 2026)])
        self.assertEqual(set(prompts[0].answers), {"t:A"})

    def test_own_goals_do_not_count(self):
        goals = [goal("m1", "A"), goal("m1", "A"), goal("m1", "A", own_goal=True)]
        self.assertEqual(t.hat_tricks(goals, [(2014, 2026)])[0].answers, {})

    def test_goals_across_matches_do_not_combine(self):
        goals = [goal("m1", "A"), goal("m1", "A"), goal("m2", "A"), goal("m2", "A")]
        self.assertEqual(t.hat_tricks(goals, [(2014, 2026)])[0].answers, {})

    def test_evidence_lists_each_hat_trick_by_season(self):
        goals = [goal("m1", "A")] * 3 + [goal("m2", "A", club="Santos", season=2019)] * 4
        self.assertEqual(t.hat_tricks(goals, [(2014, 2026)])[0].answers["t:A"], (("Santos", 2019), ("Gremio", 2023)))

    def test_each_window_only_counts_its_seasons(self):
        goals = [goal("m1", "A", season=2015)] * 3 + [goal("m2", "B", season=2024)] * 3
        early, late = t.hat_tricks(goals, [(2014, 2019), (2020, 2026)])
        self.assertEqual((set(early.answers), set(late.answers)), ({"t:A"}, {"t:B"}))
        self.assertIn("2014–2019", early.text)


class ClubSeasonTest(unittest.TestCase):
    def test_scorers_for_a_club_in_a_season(self):
        goals = [goal("m1", "A", club="Santos", season=2019), goal("m2", "B", club="Santos", season=2020),
                 goal("m3", "C", club="Gremio", season=2019), goal("m4", "D", club="Santos", season=2019, own_goal=True)]
        prompts = t.scorers_for_club(goals, PARTIAL)
        self.assertEqual(answers(prompts, "marcou-por-santos-2019"), {"t:A"})
        self.assertIn("pelo Santos no Brasileirão 2019", next(p for p in prompts if p.id == "marcou-por-santos-2019").text)

    def test_partial_season_says_where_the_data_stops(self):
        prompts = t.scorers_for_club([goal("m1", "A", club="Santos", season=2026)], PARTIAL)
        self.assertIn("2026 (até 1º de junho)", prompts[0].text)

    def test_feminine_club_names_take_pela(self):
        prompts = t.scorers_for_club([goal("m1", "A", club="Chapecoense", season=2017)], PARTIAL)
        self.assertIn("pela Chapecoense", prompts[0].text)

    def test_scorers_against_a_club_use_the_opponent_for_home_and_away_goals(self):
        matches = {"m1": match("m1", "Santos", "Gremio"), "m2": match("m2", "Gremio", "Santos")}
        goals = [goal("m1", "Home", club="Santos"), goal("m2", "Away", club="Santos"), goal("m2", "Own", club="Santos", own_goal=True)]
        prompts = t.scorers_against_club(goals, matches, PARTIAL)
        self.assertEqual(answers(prompts, "marcou-contra-gremio-2023"), {"t:Home", "t:Away"})
        self.assertIn("contra o Grêmio", next(p for p in prompts if p.id == "marcou-contra-gremio-2023").text)


class WholeWindowTest(unittest.TestCase):
    def test_penalty_scorers_for_a_club(self):
        goals = [goal("m1", "A", club="Santos", penalty=True), goal("m2", "B", club="Santos")]
        self.assertEqual(answers(t.penalty_scorers(goals, (2014, 2026)), "penalti-santos"), {"t:A"})

    def test_stoppage_time_needs_a_plus_minute_in_the_second_half(self):
        goals = [goal("m1", "A", club="Santos", minute="90+2"), goal("m2", "B", club="Santos", minute="90"),
                 goal("m3", "C", club="Santos", minute="45+1")]
        self.assertEqual(answers(t.stoppage_time_scorers(goals), "acrescimos-santos"), {"t:A"})

    def test_prolific_season_counts_one_season_at_a_time(self):
        goals = [goal(f"m{i}", "A", season=2019) for i in range(10)] + [goal(f"n{i}", "A", season=2020) for i in range(10)]
        goals += [goal(f"o{i}", "B", season=2019) for i in range(15)]
        prompts = t.prolific_seasons(goals, (2014, 2026), thresholds=(15, 12))
        self.assertEqual(answers(prompts, "gols-numa-edicao-15"), {"t:B"})
        self.assertEqual({p.family for p in prompts}, {"gols-numa-edicao"})

    def test_club_total_threshold_is_inclusive(self):
        goals = [goal(f"m{i}", "A", club="Santos") for i in range(10)] + [goal(f"n{i}", "B", club="Santos") for i in range(9)]
        self.assertEqual(answers(t.club_totals(goals, (2014, 2026), thresholds=(10,)), "gols-por-santos-10"), {"t:A"})

    def test_scorer_for_two_clubs_needs_goals_for_both(self):
        goals = [goal("m1", "A", club="Santos"), goal("m2", "A", club="Flamengo", season=2024),
                 goal("m3", "B", club="Santos"), goal("m4", "B", club="Santos")]
        prompts = t.two_club_scorers(goals, (2014, 2026), clubs=("Flamengo", "Santos"))
        self.assertEqual(answers(prompts, "marcou-por-flamengo-e-santos"), {"t:A"})
        self.assertIn("pelo Flamengo e pelo Santos", prompts[0].text)


if __name__ == "__main__":
    unittest.main()
