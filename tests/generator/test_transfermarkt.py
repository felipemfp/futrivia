import unittest

from generator import clubs
from generator.sources import transfermarkt as tm

GAMES = [
    {"game_id": "1", "competition_id": "BRA1", "season": "2024", "date": "2025-12-07", "home_club_id": "614",
     "away_club_id": "221", "home_club_goals": "2", "away_club_goals": "1"},
    {"game_id": "2", "competition_id": "BRA1", "season": "2025", "date": "2026-05-10", "home_club_id": "210",
     "away_club_id": "978", "home_club_goals": "0", "away_club_goals": "0"},
    {"game_id": "3", "competition_id": "GB1", "season": "2025", "date": "2026-05-10", "home_club_id": "1",
     "away_club_id": "2", "home_club_goals": "9", "away_club_goals": "9"},
]
PLAYERS = [{"player_id": "68290", "name": "Neymar"}, {"player_id": "7", "name": "Léo Ortiz"},
           {"player_id": "8", "name": "Pedro"}, {"player_id": "9", "name": "Rossi"}]
EVENTS = [
    {"game_id": "1", "type": "Goals", "club_id": "614", "player_id": "8", "description": ", Penalty, 1. Goal of the Season"},
    {"game_id": "1", "type": "Goals", "club_id": "614", "player_id": "7", "description": ", Own-goal"},
    {"game_id": "1", "type": "Goals", "club_id": "221", "player_id": "68290", "description": ", Header, 3. Goal of the Season"},
    {"game_id": "1", "type": "Cards", "club_id": "221", "player_id": "68290", "description": "Second yellow  , Foul"},
    {"game_id": "1", "type": "Cards", "club_id": "614", "player_id": "8", "description": "1. Yellow card  , Foul"},
    {"game_id": "1", "type": "Substitutions", "club_id": "614", "player_id": "8", "description": ""},
    {"game_id": "3", "type": "Goals", "club_id": "1", "player_id": "8", "description": ", Header"},
]
LINEUPS = [
    {"game_id": "2", "club_id": "614", "player_id": "9", "player_name": "Rossi", "type": "starting_lineup", "position": "Goalkeeper"},
    {"game_id": "2", "club_id": "614", "player_id": "8", "player_name": "Pedro", "type": "substitutes", "position": "Centre-Forward"},
]


class TransfermarktTest(unittest.TestCase):
    def setUp(self):
        self.data = tm.build(GAMES, EVENTS, LINEUPS, PLAYERS)

    def test_only_brazilian_serie_a_games_are_kept(self):
        self.assertEqual(sorted(self.data.matches), ["tm:1", "tm:2"])

    def test_season_label_is_one_year_behind_the_brasileirao(self):
        self.assertEqual(self.data.matches["tm:1"].season, 2025)
        self.assertEqual(self.data.matches["tm:2"].season, 2026)

    def test_clubs_map_to_shared_keys(self):
        self.assertEqual((self.data.matches["tm:1"].home, self.data.matches["tm:1"].away), ("Flamengo", "Santos"))

    def test_own_goal_is_flagged_and_penalty_detected(self):
        by_player = {g.player: g for g in self.data.goals}
        self.assertTrue(by_player["Léo Ortiz"].own_goal)
        self.assertTrue(by_player["Pedro"].penalty)
        self.assertFalse(by_player["Neymar"].own_goal or by_player["Neymar"].penalty)

    def test_player_refs_use_transfermarkt_ids(self):
        self.assertEqual({g.player_ref for g in self.data.goals}, {"transfermarkt:8", "transfermarkt:7", "transfermarkt:68290"})

    def test_second_yellow_counts_as_red(self):
        reds = {c.player: c.red for c in self.data.cards}
        self.assertEqual(reds, {"Neymar": True, "Pedro": False})

    def test_lineups_record_starters_and_positions(self):
        entries = {e.player: e for e in self.data.lineups}
        self.assertTrue(entries["Rossi"].starter)
        self.assertEqual(entries["Rossi"].position, "Goalkeeper")
        self.assertFalse(entries["Pedro"].starter)

    def test_player_missing_from_players_table_takes_lineup_name(self):
        lineups = LINEUPS + [{"game_id": "1", "club_id": "614", "player_id": "77", "player_name": "Wallace Yan",
                              "type": "substitutes", "position": "Centre-Forward"}]
        events = EVENTS + [{"game_id": "1", "type": "Goals", "club_id": "614", "player_id": "77", "description": ", Header"}]
        data = tm.build(GAMES, events, lineups, PLAYERS)
        self.assertIn("Wallace Yan", {g.player for g in data.goals})

    def test_player_with_no_name_anywhere_is_an_error(self):
        events = EVENTS + [{"game_id": "1", "type": "Goals", "club_id": "614", "player_id": "404", "description": ", Header"}]
        with self.assertRaises(KeyError):
            tm.build(GAMES, events, LINEUPS, PLAYERS)

    def test_unknown_club_is_an_error(self):
        games = [dict(GAMES[0], home_club_id="99999")]
        with self.assertRaises(KeyError):
            tm.build(games, [], [], PLAYERS)

    def test_every_mapped_club_has_a_display_name(self):
        for key in clubs.TRANSFERMARKT.values():
            self.assertTrue(clubs.display(key))


if __name__ == "__main__":
    unittest.main()
