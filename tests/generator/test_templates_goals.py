import unittest

from generator.records import Goal
from generator.templates.goals import hat_tricks


def goal(match, player, own_goal=False, club="Gremio", season=2023):
    return Goal(match_id=match, season=season, date=f"{season}-06-01", club=club, player=player,
                player_ref=f"t:{player}", minute="1", penalty=False, own_goal=own_goal)


class HatTrickTest(unittest.TestCase):
    def test_three_goals_in_one_match_is_a_hat_trick(self):
        prompt = hat_tricks([goal("m1", "A")] * 3)
        self.assertEqual(set(prompt.answers), {"t:A"})

    def test_own_goals_do_not_count(self):
        goals = [goal("m1", "A"), goal("m1", "A"), goal("m1", "A", own_goal=True)]
        self.assertEqual(hat_tricks(goals).answers, {})

    def test_goals_across_matches_do_not_combine(self):
        goals = [goal("m1", "A"), goal("m1", "A"), goal("m2", "A"), goal("m2", "A")]
        self.assertEqual(hat_tricks(goals).answers, {})

    def test_evidence_lists_each_hat_trick_by_season(self):
        goals = [goal("m1", "A")] * 3 + [goal("m2", "A", club="Santos", season=2019)] * 4
        self.assertEqual(hat_tricks(goals).answers["t:A"], (("Santos", 2019), ("Gremio", 2023)))

    def test_text_states_data_window_from_the_data(self):
        goals = [goal("m1", "A", season=2015)] * 3 + [goal("m2", "B", season=2024)]
        self.assertIn("2015–2024", hat_tricks(goals).text)


if __name__ == "__main__":
    unittest.main()
